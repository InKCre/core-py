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


class Newsletter(BaseModel):
    """Newsletter data model."""

    subject: str
    """Newsletter subject"""
    body: str
    """Newsletter body (plain text preferred, HTML fallback)"""

    __resolver__: typing.ClassVar[typing.Any] = None
