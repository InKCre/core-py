"""Telegram legacy content, Source state, and attachment metadata."""

from __future__ import annotations

import datetime
import typing

import pydantic
from app.schemas.info_base.block import BlockModel


class TelegramMessage(pydantic.BaseModel):
  """Published 0.1.0 content shape retained for read compatibility."""

  message_id: int
  date: datetime.datetime
  text: str | None = None
  caption: str | None = None
  reply_to_message_id: int | None = None
  has_media: bool = False
  media_type: str | None = None

  __resolver__: typing.ClassVar[typing.Any] = None


class TelegramSourceConfig(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid")

  bot_token: str = pydantic.Field(min_length=1)
  bound_user_id: int = pydantic.Field(gt=0)
  download_attachments: bool = False


class TelegramSourceState(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="allow")

  bot_id: int | None = pydantic.Field(default=None, gt=0)
  last_update_id: int | None = pydantic.Field(default=None, ge=0)

  @pydantic.model_validator(mode="after")
  def require_bot_scoped_cursor(self) -> TelegramSourceState:
    if self.last_update_id is not None and self.bot_id is None:
      raise ValueError("last_update_id has no pinned bot_id; create a new Source")
    return self


AttachmentKind = typing.Literal[
  "photo",
  "animation",
  "audio",
  "document",
  "sticker",
  "video",
  "video_note",
  "voice",
]


class TelegramAttachment(pydantic.BaseModel):
  """Retrieval and later-materialization facts for one Telegram file."""

  model_config = pydantic.ConfigDict(extra="forbid")

  kind: AttachmentKind
  file_id: str = pydantic.Field(min_length=1)
  file_unique_id: str = pydantic.Field(min_length=1)
  filename: str | None = None
  mime_type: str | None = None
  file_size: int | None = pydantic.Field(default=None, ge=0)
  width: int | None = pydantic.Field(default=None, ge=0)
  height: int | None = pydantic.Field(default=None, ge=0)
  duration: int | None = pydantic.Field(default=None, ge=0)
  title: str | None = None
  performer: str | None = None
  emoji: str | None = None


class SolvedTelegramAttachment(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

  root: TelegramAttachment
  content: BlockModel | None = None


class TelegramAttachmentMaterializeRequest(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid")

  block: int
