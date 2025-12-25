"""InKCre Mail Extension Schemas."""

__all__ = [
  "EmailAddress",
  "Email",
  "Newsletter",
]

from datetime import datetime
from typing import Optional as Opt
import sqlmodel
import pydantic


class EmailAddress(sqlmodel.SQLModel):
  """Email address."""

  email: str
  """Normalized email address (lowercase)"""
  name: Opt[str] = None
  """Display name for the email address"""

  @pydantic.field_validator("email")
  @classmethod
  def normalize_email(cls, v: str) -> str:
    """Normalize email address to lowercase."""
    return v.lower().strip()


class Email(sqlmodel.SQLModel):
  """Email block content model."""

  uid: int
  """Unique identifier from IMAP server"""
  message_id: str
  """Email message ID from headers"""
  subject: str
  """Email subject"""
  date: datetime
  """Email date"""
  body_text: Opt[str] = None
  """Plain text body"""
  body_html: Opt[str] = None
  """HTML body"""
  has_attachments: bool = False
  """Whether email has attachments"""


class Newsletter(sqlmodel.SQLModel):
  """Newsletter data model."""

  subject: str
  """Newsletter subject"""
  body: str
  """Newsletter body (plain text preferred, HTML fallback)"""
