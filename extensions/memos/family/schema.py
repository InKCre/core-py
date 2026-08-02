"""Canonical memo-family values persisted in the info-base graph."""

import datetime
import enum

import pydantic


class MemoVisibility(enum.StrEnum):
  PRIVATE = "private"
  PROTECTED = "protected"
  PUBLIC = "public"


class CanonicalMemo(pydantic.BaseModel):
  """Exact v1 root content; graph-owned links are intentionally absent."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  body: str
  created_at: datetime.datetime | None
  updated_at: datetime.datetime | None
  archived: bool = False
  visibility: MemoVisibility = MemoVisibility.PRIVATE
  pinned: bool = False

  @pydantic.field_validator("created_at", "updated_at")
  @classmethod
  def require_utc(cls, value: datetime.datetime | None) -> datetime.datetime | None:
    if value is None:
      return None
    if value.tzinfo is None or value.utcoffset() is None:
      raise ValueError("memo timestamps must include an RFC3339 timezone")
    return value.astimezone(datetime.UTC)

  def to_block_content(self) -> str:
    """Serialize the authoritative root content deterministically."""
    return self.model_dump_json()

  @classmethod
  def from_block_content(cls, content: str) -> "CanonicalMemo":
    return cls.model_validate_json(content)


class CanonicalAttachment(pydantic.BaseModel):
  """Memos-authored attachment metadata; actual content remains graph-owned."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  filename: str
  media_type: str
  size: int = pydantic.Field(ge=0)
  created_at: datetime.datetime

  @pydantic.field_validator("created_at")
  @classmethod
  def require_utc(cls, value: datetime.datetime) -> datetime.datetime:
    normalized = CanonicalMemo.require_utc(value)
    if normalized is None:
      raise ValueError("attachment created_at is required")
    return normalized

  def to_block_content(self) -> str:
    return self.model_dump_json()

  @classmethod
  def from_block_content(cls, content: str) -> "CanonicalAttachment":
    return cls.model_validate_json(content)


class SolvedAttachment(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(frozen=True)

  block_id: int
  content_block_id: int
  canonical: CanonicalAttachment
  owner_memo_id: int | None = None


class SolvedMemo(pydantic.BaseModel):
  """Resolver projection of one memo root and its graph-owned links."""

  model_config = pydantic.ConfigDict(frozen=True)

  block_id: int
  canonical: CanonicalMemo
  attachments: tuple[SolvedAttachment, ...] = ()
  parent_id: int | None = None
  reference_ids: tuple[int, ...] = ()

  @property
  def attachment_ids(self) -> tuple[int, ...]:
    return tuple(attachment.block_id for attachment in self.attachments)


class CanonicalMemoPatch(pydantic.BaseModel):
  """Selected CanonicalMemo root changes; field presence is authoritative."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  body: str | None = None
  updated_at: datetime.datetime | None = None
  archived: bool | None = None
  visibility: MemoVisibility | None = None
  pinned: bool | None = None

  @pydantic.model_validator(mode="after")
  def selected_fields_cannot_be_null(self) -> "CanonicalMemoPatch":
    for field in self.model_fields_set:
      if getattr(self, field) is None:
        raise ValueError(f"selected memo field cannot be null: {field}")
    if not self.model_fields_set:
      raise ValueError("memo patch must select at least one root field")
    return self

  @pydantic.field_validator("updated_at")
  @classmethod
  def require_utc(cls, value: datetime.datetime | None) -> datetime.datetime | None:
    return CanonicalMemo.require_utc(value)

  def apply(self, canonical: CanonicalMemo) -> CanonicalMemo:
    changes = {field: getattr(self, field) for field in self.model_fields_set}
    return canonical.model_copy(update=changes)


class MemoCursor(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(frozen=True)

  created_at: datetime.datetime | None
  block_id: int = pydantic.Field(gt=0)

  @pydantic.field_validator("created_at")
  @classmethod
  def require_utc(cls, value: datetime.datetime | None) -> datetime.datetime | None:
    return CanonicalMemo.require_utc(value)


class MemoPage(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(frozen=True)

  memos: tuple[SolvedMemo, ...]
  next_cursor: MemoCursor | None


class CommentPage(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(frozen=True)

  comments: tuple[SolvedMemo, ...]
  next_block_id: int | None
  total_size: int = pydantic.Field(ge=0)
