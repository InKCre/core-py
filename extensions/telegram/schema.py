"""Schema definitions for Telegram message data."""

import typing
from datetime import datetime
from typing import Optional as Opt
from pydantic import BaseModel, ConfigDict


class TelegramUser(BaseModel):
    """Represents a Telegram user."""
    id: int
    """Telegram user ID"""
    first_name: str
    """User's first name"""
    last_name: Opt[str] = None
    """User's last name"""
    username: Opt[str] = None
    """User's username"""
    is_bot: bool = False
    """True if this user is a bot"""


class TelegramChat(BaseModel):
    """Represents a Telegram chat."""
    id: int
    """Unique identifier for this chat"""
    type: str
    """Type of chat (private, group, supergroup, or channel)"""
    title: Opt[str] = None
    """Title for groups, supergroups and channels"""
    username: Opt[str] = None
    """Username for private chats, supergroups and channels if available"""


class TelegramMessage(BaseModel):
    """Telegram message data model."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "message_id": 12345,
            "date": "2024-01-01T12:00:00",
            "chat": {"id": 123, "type": "private"},
            "from_user": {"id": 456, "first_name": "John", "username": "john_doe"},
            "text": "Hello from Telegram!",
        }
    })

    message_id: int
    """Unique message identifier inside this chat"""
    date: datetime
    """Date the message was sent"""
    chat: TelegramChat
    """Conversation the message belongs to"""
    from_user: Opt[TelegramUser] = None
    """Sender of the message (empty for messages sent to channels)"""
    text: Opt[str] = None
    """Text content of the message"""
    caption: Opt[str] = None
    """Caption for photos, videos, documents, etc."""
    forward_from: Opt[TelegramUser] = None
    """For forwarded messages, sender of the original message"""
    reply_to_message_id: Opt[int] = None
    """If the message is a reply, ID of the original message"""
    has_media: bool = False
    """Whether the message contains media (photo, video, document, etc.)"""
    media_type: Opt[str] = None
    """Type of media if present (photo, video, document, audio, etc.)"""

    __resolver__: typing.ClassVar[typing.Any] = None
