"""Schema definitions for Telegram message data."""

import typing
from datetime import datetime
from typing import Optional as Opt
from pydantic import BaseModel


class TelegramMessage(BaseModel):
  """Telegram message data model.

  Stores only the message content without user/chat information.
  """

  message_id: int
  """Unique message identifier"""
  date: datetime
  """Date the message was sent"""
  text: Opt[str] = None
  """Text content of the message"""
  caption: Opt[str] = None
  """Caption for photos, videos, documents, etc."""
  reply_to_message_id: Opt[int] = None
  """If the message is a reply, ID of the original message"""
  has_media: bool = False
  """Whether the message contains media (photo, video, document, etc.)"""
  media_type: Opt[str] = None
  """Type of media if present (photo, video, document, audio, etc.)"""

  __resolver__: typing.ClassVar[typing.Any] = None
