"""Opaque Memos 0.29.1 list cursor bound to the accepted query."""

import base64
import typing

import pydantic

from extensions.memos.family import MemoCursor


CREATOR_FILTER = 'creator == "users/inkcre"'


class PageToken(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  version: typing.Literal[1] = 1
  generation: typing.Literal["memos-0.29.1"] = "memos-0.29.1"
  state: typing.Literal["NORMAL", "ARCHIVED"]
  filter: typing.Literal['creator == "users/inkcre"']
  cursor: MemoCursor


class CommentPageToken(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  version: typing.Literal[1] = 1
  generation: typing.Literal["memos-0.29.1-comments"] = "memos-0.29.1-comments"
  parent_id: int = pydantic.Field(gt=0)
  after_block_id: int = pydantic.Field(gt=0)


def encode_page_token(
  cursor: MemoCursor,
  *,
  state: typing.Literal["NORMAL", "ARCHIVED"],
  filter_: str,
) -> str:
  token = PageToken(
    state=state,
    filter=typing.cast(typing.Literal['creator == "users/inkcre"'], filter_),
    cursor=cursor,
  )
  raw = token.model_dump_json().encode()
  return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_page_token(
  value: str,
  *,
  state: typing.Literal["NORMAL", "ARCHIVED"],
  filter_: str,
) -> MemoCursor:
  try:
    padding = "=" * (-len(value) % 4)
    raw = base64.b64decode(value + padding, altchars=b"-_", validate=True)
    token = PageToken.model_validate_json(raw)
  except (ValueError, pydantic.ValidationError) as error:
    raise ValueError("Invalid page token") from error
  if token.state != state or token.filter != filter_:
    raise ValueError("Page token does not belong to this memo query")
  return token.cursor


def parse_list_query(
  query: dict[str, str],
) -> tuple[
  int,
  typing.Literal["NORMAL", "ARCHIVED"],
  str,
  MemoCursor | None,
]:
  unknown = set(query) - {"pageSize", "pageToken", "state", "filter"}
  if unknown:
    raise ValueError(f"Unsupported list query: {sorted(unknown)[0]}")
  try:
    requested_size = int(query.get("pageSize", "50"))
  except ValueError as error:
    raise ValueError("pageSize must be an integer") from error
  page_size = 50 if requested_size <= 0 else min(requested_size, 1000)

  raw_state = query.get("state", "NORMAL")
  if raw_state not in {"NORMAL", "ARCHIVED"}:
    raise ValueError("state must be NORMAL or ARCHIVED")
  state = typing.cast(typing.Literal["NORMAL", "ARCHIVED"], raw_state)

  filter_ = query.get("filter", "")
  if filter_ != CREATOR_FILTER:
    raise ValueError("filter must select the deployment creator")

  raw_token = query.get("pageToken")
  cursor = decode_page_token(raw_token, state=state, filter_=filter_) if raw_token else None
  return page_size, state, filter_, cursor


def encode_comment_page_token(
  after_block_id: int,
  *,
  parent_id: int,
) -> str:
  raw = (
    CommentPageToken(
      parent_id=parent_id,
      after_block_id=after_block_id,
    )
    .model_dump_json()
    .encode()
  )
  return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_comment_page_token(value: str, *, parent_id: int) -> int:
  try:
    padding = "=" * (-len(value) % 4)
    raw = base64.b64decode(value + padding, altchars=b"-_", validate=True)
    token = CommentPageToken.model_validate_json(raw)
  except (ValueError, pydantic.ValidationError) as error:
    raise ValueError("Invalid comment page token") from error
  if token.parent_id != parent_id:
    raise ValueError("Comment page token does not belong to this parent memo")
  return token.after_block_id


def parse_comment_list_query(
  query: dict[str, str],
  *,
  parent_id: int,
) -> tuple[int, int | None]:
  unknown = set(query) - {"pageSize", "pageToken", "orderBy"}
  if unknown:
    raise ValueError(f"Unsupported comment list query: {sorted(unknown)[0]}")
  if query.get("orderBy", ""):
    raise ValueError("Custom comment orderBy is not supported")
  try:
    requested_size = int(query.get("pageSize", "10"))
  except ValueError as error:
    raise ValueError("pageSize must be an integer") from error
  page_size = 10 if requested_size <= 0 else min(requested_size, 1000)

  raw_token = query.get("pageToken")
  after_block_id = (
    decode_comment_page_token(raw_token, parent_id=parent_id) if raw_token else None
  )
  return page_size, after_block_id
