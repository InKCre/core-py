"""Schema definitions for email data."""

import typing
from datetime import datetime
from typing import Optional as Opt
from pydantic import BaseModel, ConfigDict


class EmailAddress(BaseModel):
    """Represents an email address with optional name."""
    email: str
    name: Opt[str] = None


class Email(BaseModel):
    """Email data model."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "uid": 12345,
            "message_id": "<abc123@example.com>",
            "subject": "Test Email",
            "from_": {"email": "sender@example.com", "name": "Sender Name"},
            "to": [{"email": "recipient@example.com", "name": "Recipient"}],
            "date": "2024-01-01T12:00:00",
            "body_text": "This is the email body.",
            "has_attachments": False
        }
    })

    uid: int
    """Unique identifier from IMAP server"""
    message_id: str
    """Email message ID from headers"""
    subject: str
    """Email subject"""
    from_: EmailAddress
    """Sender email address"""
    to: list[EmailAddress]
    """List of recipient email addresses"""
    cc: list[EmailAddress] = []
    """List of CC email addresses"""
    date: datetime
    """Email date"""
    body_text: Opt[str] = None
    """Plain text body"""
    body_html: Opt[str] = None
    """HTML body"""
    has_attachments: bool = False
    """Whether email has attachments"""

    __resolver__: typing.ClassVar[typing.Any] = None
