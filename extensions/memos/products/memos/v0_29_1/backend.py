"""Memos 0.29.1 backend route composition."""

import base64
import binascii

import fastapi
import pydantic

from extensions.memos.auth import require_memos_pat
from extensions.memos.family import (
  AttachmentApplicationService,
  AttachmentNotFoundError,
  AttachmentOwnershipError,
  MemoApplicationService,
  MemoNotFoundError,
)
from .adapter import (
  attachment_from_solved,
  attachment_id,
  attachment_ids,
  canonical_from_create,
  memo_from_solved,
  update_plan,
)
from .pagination import (
  encode_comment_page_token,
  encode_page_token,
  parse_comment_list_query,
  parse_list_query,
)
from .wire import (
  CreateMemoRequest,
  CreateAttachmentRequest,
  GetCurrentUserResponse,
  InstanceProfile,
  ListMemosResponse,
  ListMemoCommentsResponse,
  ListAttachmentsResponse,
  Attachment,
  Memo,
  UpdateMemoRequest,
  UserSetting,
)


MAX_ATTACHMENT_BYTES = 32 * 1024 * 1024
MAX_ATTACHMENT_REQUEST_BYTES = 45 * 1024 * 1024


def _bad_request(detail: object) -> fastapi.HTTPException:
  return fastapi.HTTPException(
    status_code=fastapi.status.HTTP_400_BAD_REQUEST,
    detail=detail,
  )


async def _parse_create_request(request: fastapi.Request) -> CreateMemoRequest:
  payload = await _parse_json_object(request)
  try:
    return CreateMemoRequest.model_validate(payload)
  except pydantic.ValidationError as error:
    raise _bad_request(error.errors(include_context=False)) from error


async def _parse_update_request(
  request: fastapi.Request,
) -> tuple[UpdateMemoRequest, set[str]]:
  payload = await _parse_json_object(request)
  try:
    return UpdateMemoRequest.model_validate(payload), set(payload)
  except pydantic.ValidationError as error:
    raise _bad_request(error.errors(include_context=False)) from error


async def _parse_json_object(request: fastapi.Request) -> dict:
  try:
    payload = await request.json()
    if not isinstance(payload, dict):
      raise ValueError("body is not an object")
    return payload
  except ValueError as error:
    raise _bad_request("Request body must be valid JSON") from error


def _memo_id(raw_id: str) -> int:
  try:
    block_id = int(raw_id)
  except ValueError as error:
    raise _bad_request("Memo name must contain an integer block ID") from error
  if block_id <= 0 or str(block_id) != raw_id:
    raise _bad_request("Memo block ID must be positive")
  return block_id


def _validate_attachment_metadata(filename: str, media_type: str) -> None:
  if (
    not filename
    or len(filename) > 1024
    or filename in {".", ".."}
    or any(character in filename for character in ("/", "\\", "\x00"))
  ):
    raise ValueError("filename must be a non-path attachment name")
  if (
    not media_type
    or len(media_type) > 255
    or "/" not in media_type
    or "\r" in media_type
    or "\n" in media_type
  ):
    raise ValueError("type must be a valid media type")


async def _parse_attachment_upload(
  request: fastapi.Request,
) -> tuple[CreateAttachmentRequest, bytes]:
  raw = await request.body()
  if len(raw) > MAX_ATTACHMENT_REQUEST_BYTES:
    raise fastapi.HTTPException(
      status_code=fastapi.status.HTTP_413_CONTENT_TOO_LARGE,
      detail="Attachment request exceeds the 32 MiB decoded limit",
    )
  try:
    body = CreateAttachmentRequest.model_validate_json(raw)
    _validate_attachment_metadata(body.filename, body.type)
    content = base64.b64decode(body.content, validate=True)
  except pydantic.ValidationError as error:
    raise _bad_request(error.errors(include_context=False)) from error
  except (ValueError, binascii.Error) as error:
    raise _bad_request(str(error)) from error
  if len(content) > MAX_ATTACHMENT_BYTES:
    raise fastapi.HTTPException(
      status_code=fastapi.status.HTTP_413_CONTENT_TOO_LARGE,
      detail="Attachment exceeds the 32 MiB decoded limit",
    )
  return body, content


def _not_found(error: LookupError) -> fastapi.HTTPException:
  return fastapi.HTTPException(
    status_code=fastapi.status.HTTP_404_NOT_FOUND,
    detail=str(error),
  )


def register_backend(root: fastapi.APIRouter) -> None:
  """Attach the public probe and PAT-protected 0.29.1 route groups."""
  public = fastapi.APIRouter(prefix="/api/v1")
  protected = fastapi.APIRouter(
    prefix="/api/v1",
    dependencies=[fastapi.Depends(require_memos_pat)],
  )
  protected_files = fastapi.APIRouter(
    prefix="/file",
    dependencies=[fastapi.Depends(require_memos_pat)],
  )

  @public.get("/instance/profile", response_model=InstanceProfile)
  def get_instance_profile() -> InstanceProfile:
    return InstanceProfile()

  @protected.get("/auth/me", response_model=GetCurrentUserResponse)
  def get_current_user() -> GetCurrentUserResponse:
    return GetCurrentUserResponse()

  @protected.get(
    "/users/{user_id}/settings/GENERAL",
    response_model=UserSetting,
  )
  def get_general_settings(user_id: str) -> UserSetting:
    if user_id != "inkcre":
      raise fastapi.HTTPException(
        status_code=fastapi.status.HTTP_404_NOT_FOUND,
        detail=f"User users/{user_id} not found",
      )
    return UserSetting()

  @protected.post(
    "/memos",
    response_model=Memo,
    response_model_exclude_none=True,
  )
  async def create_memo(request: fastapi.Request) -> Memo:
    body = await _parse_create_request(request)
    try:
      canonical = canonical_from_create(body)
      requested_attachments = attachment_ids(body.attachments)
    except ValueError as error:
      raise _bad_request(str(error)) from error
    try:
      solved = await MemoApplicationService.create(
        canonical,
        attachment_ids=requested_attachments,
      )
    except AttachmentNotFoundError as error:
      raise _not_found(error) from error
    except AttachmentOwnershipError as error:
      raise _bad_request(str(error)) from error
    return memo_from_solved(solved)

  @protected.get(
    "/memos",
    response_model=ListMemosResponse,
    response_model_exclude_none=True,
  )
  async def list_memos(request: fastapi.Request) -> ListMemosResponse:
    try:
      page_size, state, filter_, cursor = parse_list_query(dict(request.query_params))
    except ValueError as error:
      raise _bad_request(str(error)) from error
    page = await MemoApplicationService.list_top_level(
      archived=state == "ARCHIVED",
      limit=page_size,
      after=cursor,
    )
    next_page_token = (
      encode_page_token(
        page.next_cursor,
        state=state,
        filter_=filter_,
      )
      if page.next_cursor is not None
      else ""
    )
    return ListMemosResponse(
      memos=[memo_from_solved(memo) for memo in page.memos],
      next_page_token=next_page_token,
    )

  @protected.patch(
    "/memos/{raw_memo_id}",
    response_model=Memo,
    response_model_exclude_none=True,
  )
  async def update_memo(raw_memo_id: str, request: fastapi.Request) -> Memo:
    block_id = _memo_id(raw_memo_id)
    body, raw_keys = await _parse_update_request(request)
    raw_mask = (
      request.query_params.get("updateMask")
      if "updateMask" in request.query_params
      else None
    )
    try:
      plan = update_plan(
        body,
        raw_keys=raw_keys,
        update_mask=raw_mask,
      )
    except ValueError as error:
      raise _bad_request(str(error)) from error
    requested_attachments = None
    if plan.replace_attachments:
      try:
        requested_attachments = tuple(attachment_id(name) for name in plan.attachments)
      except ValueError as error:
        raise _bad_request(str(error)) from error
    try:
      solved = await MemoApplicationService.update(
        block_id,
        plan.root_patch,
        attachment_ids=requested_attachments,
      )
    except MemoNotFoundError as error:
      raise _not_found(error) from error
    except AttachmentNotFoundError as error:
      raise _not_found(error) from error
    except AttachmentOwnershipError as error:
      raise _bad_request(str(error)) from error
    return memo_from_solved(solved)

  @protected.post(
    "/memos/{raw_parent_id}/comments",
    response_model=Memo,
    response_model_exclude_none=True,
  )
  async def create_memo_comment(
    raw_parent_id: str,
    request: fastapi.Request,
  ) -> Memo:
    parent_id = _memo_id(raw_parent_id)
    body = await _parse_create_request(request)
    try:
      canonical = canonical_from_create(body)
      requested_attachments = attachment_ids(body.attachments)
    except ValueError as error:
      raise _bad_request(str(error)) from error
    try:
      solved = await MemoApplicationService.create_comment(
        parent_id,
        canonical,
        attachment_ids=requested_attachments,
      )
    except MemoNotFoundError as error:
      raise _not_found(error) from error
    except AttachmentNotFoundError as error:
      raise _not_found(error) from error
    except AttachmentOwnershipError as error:
      raise _bad_request(str(error)) from error
    return memo_from_solved(solved)

  @protected.get(
    "/memos/{raw_parent_id}/comments",
    response_model=ListMemoCommentsResponse,
    response_model_exclude_none=True,
  )
  async def list_memo_comments(
    raw_parent_id: str,
    request: fastapi.Request,
  ) -> ListMemoCommentsResponse:
    parent_id = _memo_id(raw_parent_id)
    try:
      limit, after_block_id = parse_comment_list_query(
        dict(request.query_params),
        parent_id=parent_id,
      )
      page = await MemoApplicationService.list_comments(
        parent_id,
        limit=limit,
        after_block_id=after_block_id,
      )
    except ValueError as error:
      raise _bad_request(str(error)) from error
    except MemoNotFoundError as error:
      raise _not_found(error) from error
    return ListMemoCommentsResponse(
      memos=[memo_from_solved(comment) for comment in page.comments],
      next_page_token=(
        encode_comment_page_token(page.next_block_id, parent_id=parent_id)
        if page.next_block_id is not None
        else ""
      ),
      total_size=page.total_size,
    )

  @protected.delete("/memos/{raw_memo_id}")
  def delete_memo(raw_memo_id: str, request: fastapi.Request) -> dict:
    if request.query_params:
      raise _bad_request("Delete memo query parameters are not supported")
    block_id = _memo_id(raw_memo_id)
    try:
      MemoApplicationService.delete(block_id)
    except MemoNotFoundError as error:
      raise _not_found(error) from error
    return {}

  @protected.post(
    "/attachments",
    response_model=Attachment,
    response_model_exclude_none=True,
  )
  async def create_attachment(request: fastapi.Request) -> Attachment:
    body, content = await _parse_attachment_upload(request)
    try:
      memo_id = _memo_id(body.memo.removeprefix("memos/")) if body.memo else None
      if body.memo is not None and body.memo != f"memos/{memo_id}":
        raise ValueError(f"Invalid memo resource name: {body.memo}")
      solved = await AttachmentApplicationService.create(
        filename=body.filename,
        media_type=body.type,
        content=content,
        memo_id=memo_id,
      )
    except AttachmentNotFoundError as error:
      raise _not_found(error) from error
    except ValueError as error:
      raise _bad_request(str(error)) from error
    return attachment_from_solved(solved)

  @protected.get(
    "/attachments",
    response_model=ListAttachmentsResponse,
    response_model_exclude_none=True,
  )
  async def list_attachments() -> ListAttachmentsResponse:
    attachments = await AttachmentApplicationService.list()
    return ListAttachmentsResponse(
      attachments=[attachment_from_solved(item) for item in attachments]
    )

  @protected.delete("/attachments/{raw_attachment_id}")
  def delete_attachment(raw_attachment_id: str) -> dict:
    attachment_id_value = _memo_id(raw_attachment_id)
    try:
      AttachmentApplicationService.delete(attachment_id_value)
    except AttachmentNotFoundError as error:
      raise _not_found(error) from error
    return {}

  @protected_files.get("/attachments/{raw_attachment_id}/{filename}")
  async def download_attachment(
    raw_attachment_id: str,
    filename: str,
  ) -> fastapi.Response:
    attachment_id_value = _memo_id(raw_attachment_id)
    try:
      media_type, content = await AttachmentApplicationService.download(
        attachment_id_value,
        filename,
      )
    except AttachmentNotFoundError as error:
      raise _not_found(error) from error
    return fastapi.Response(content=content, media_type=media_type)

  root.include_router(public)
  root.include_router(protected)
  root.include_router(protected_files)
