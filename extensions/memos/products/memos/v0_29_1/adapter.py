"""Pure mapping between Memos 0.29.1 wire values and memo-family values."""

import datetime
from dataclasses import dataclass
import typing

from extensions.memos.family import (
  CanonicalMemo,
  CanonicalMemoPatch,
  MemoVisibility,
  SolvedAttachment,
  SolvedMemo,
)
from .wire import (
  Attachment,
  CreateMemoRequest,
  Memo,
  MemosVisibility,
  UpdateMemoRequest,
)


def canonical_from_create(
  request: CreateMemoRequest,
  *,
  now: datetime.datetime | None = None,
) -> CanonicalMemo:
  timestamp = request.create_time or now or datetime.datetime.now(datetime.UTC)
  if timestamp.tzinfo is None or timestamp.utcoffset() is None:
    raise ValueError("createTime must include an RFC3339 timezone")
  timestamp = timestamp.astimezone(datetime.UTC)
  visibility = MemoVisibility((request.visibility or "PRIVATE").lower())
  return CanonicalMemo(
    body=request.content,
    created_at=timestamp,
    updated_at=timestamp,
    archived=False,
    visibility=visibility,
    pinned=False,
  )


def memo_from_solved(solved: SolvedMemo) -> Memo:
  canonical = solved.canonical
  return Memo(
    name=f"memos/{solved.block_id}",
    state="ARCHIVED" if canonical.archived else "NORMAL",
    create_time=canonical.created_at,
    update_time=canonical.updated_at,
    content=canonical.body,
    visibility=typing.cast(MemosVisibility, canonical.visibility.value.upper()),
    pinned=canonical.pinned,
    attachments=[attachment_from_solved(item) for item in solved.attachments],
    parent=(f"memos/{solved.parent_id}" if solved.parent_id is not None else None),
  )


def attachment_from_solved(solved: SolvedAttachment) -> Attachment:
  canonical = solved.canonical
  return Attachment(
    name=f"attachments/{solved.block_id}",
    create_time=canonical.created_at,
    filename=canonical.filename,
    type=canonical.media_type,
    size=str(canonical.size),
    memo=(f"memos/{solved.owner_memo_id}" if solved.owner_memo_id is not None else None),
  )


def attachment_id(name: str) -> int:
  prefix = "attachments/"
  if not name.startswith(prefix):
    raise ValueError(f"Invalid attachment resource name: {name}")
  raw_id = name.removeprefix(prefix)
  try:
    value = int(raw_id)
  except ValueError as error:
    raise ValueError(f"Invalid attachment resource name: {name}") from error
  if value <= 0 or str(value) != raw_id:
    raise ValueError(f"Invalid attachment resource name: {name}")
  return value


def attachment_ids(attachments: list[Attachment] | None) -> tuple[int, ...]:
  values = tuple(
    attachment_id(attachment.name)
    for attachment in attachments or []
    if attachment.name is not None
  )
  if len(values) != len(attachments or []):
    raise ValueError("Every attachment must have a resource name")
  if len(set(values)) != len(values):
    raise ValueError("Attachment list contains duplicate identities")
  return values


@dataclass(frozen=True)
class MemoUpdatePlan:
  root_patch: CanonicalMemoPatch | None
  replace_attachments: bool
  attachments: tuple[str, ...]


_UPDATE_FIELDS = {
  "content",
  "visibility",
  "state",
  "pinned",
  "updateTime",
  "attachments",
}
_MASK_ALIASES = {"update_time": "updateTime"}


def update_plan(
  request: UpdateMemoRequest,
  *,
  raw_keys: set[str],
  update_mask: str | None,
  now: datetime.datetime | None = None,
) -> MemoUpdatePlan:
  if update_mask is None:
    selected = raw_keys
  else:
    if not update_mask:
      raise ValueError("updateMask must not be empty")
    selected = {
      _MASK_ALIASES.get(path.strip(), path.strip()) for path in update_mask.split(",")
    }
    if "" in selected:
      raise ValueError("updateMask contains an empty path")
  unknown = selected - _UPDATE_FIELDS
  if unknown:
    raise ValueError(f"Unsupported updateMask path: {sorted(unknown)[0]}")
  if not selected:
    raise ValueError("updateMask must select at least one field")

  values = request.model_dump(by_alias=True)
  for field in selected & raw_keys:
    if values[field] is None:
      raise ValueError(f"Selected memo field cannot be null: {field}")

  patch_values: dict[str, object] = {}
  if "content" in selected:
    patch_values["body"] = request.content if "content" in raw_keys else ""
  if "visibility" in selected:
    visibility = request.visibility if "visibility" in raw_keys else "PRIVATE"
    patch_values["visibility"] = MemoVisibility(
      typing.cast(MemosVisibility, visibility).lower()
    )
  if "state" in selected:
    state = request.state if "state" in raw_keys else "NORMAL"
    patch_values["archived"] = state == "ARCHIVED"
  if "pinned" in selected:
    patch_values["pinned"] = request.pinned if "pinned" in raw_keys else False
  if "updateTime" in selected:
    timestamp = request.update_time if "updateTime" in raw_keys else None
    patch_values["updated_at"] = timestamp or now or datetime.datetime.now(datetime.UTC)

  root_patch = CanonicalMemoPatch.model_validate(patch_values) if patch_values else None
  replace_attachments = "attachments" in selected
  attachment_names = ()
  if replace_attachments:
    attachments = request.attachments if "attachments" in raw_keys else []
    attachment_names = tuple(
      attachment.name for attachment in attachments or [] if attachment.name is not None
    )
    attachment_ids(attachments)

  return MemoUpdatePlan(
    root_patch=root_patch,
    replace_attachments=replace_attachments,
    attachments=attachment_names,
  )
