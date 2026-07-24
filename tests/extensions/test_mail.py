"""Tests for mail extension."""

import os

# Set a dummy database connection string to avoid engine creation error
os.environ.setdefault("DB_CONN_STRING", "sqlite:///:memory:")

# Initialize logger before importing extensions
from libs.obsrv.main import setup_obsrv

setup_obsrv()

from extensions.mail.schema import Email, EmailAddress
from datetime import datetime
from email.message import EmailMessage
import asyncio


def test_email_schema():
  """Test email schema creation."""
  email = Email(
    uid=12345,
    message_id="<test@example.com>",
    subject="Test Email",
    date=datetime(2024, 1, 1, 12, 0, 0),
    body_text="This is a test email.",
    has_attachments=False,
  )

  assert email.uid == 12345
  assert email.subject == "Test Email"
  assert email.date == datetime(2024, 1, 1, 12, 0, 0)


def test_email_address_schema():
  """Test email address schema."""
  addr = EmailAddress(email="test@example.com", name="Test User")

  assert addr.email == "test@example.com"
  assert addr.name == "Test User"

  # Test without name
  addr2 = EmailAddress(email="test2@example.com")
  assert addr2.email == "test2@example.com"
  assert addr2.name is None


def test_email_serialization():
  """Test email JSON serialization."""
  email = Email(
    uid=12345,
    message_id="<test@example.com>",
    subject="Test Email",
    date=datetime(2024, 1, 1, 12, 0, 0),
    body_text="This is a test email.",
    has_attachments=False,
  )

  json_str = email.model_dump_json()
  assert json_str is not None
  assert isinstance(json_str, str)

  # Test deserialization
  email2 = Email.model_validate_json(json_str)
  assert email2.uid == email.uid
  assert email2.subject == email.subject


def test_body_types_text_only():
  """Test that body_types='text' extracts only plain text body."""
  from extensions.mail.imap import Source as ImapSource

  # Create a multipart email with both text and HTML
  msg = EmailMessage()
  msg.set_content("This is plain text")
  msg.add_alternative("<html><body>This is HTML</body></html>", subtype="html")

  # Extract with text only
  body_text, body_html = ImapSource._get_email_body(msg, body_types="text")

  assert body_text is not None
  assert body_text.strip() == "This is plain text"
  assert body_html is None


def test_body_types_html_only():
  """Test that body_types='html' extracts only HTML body."""
  from extensions.mail.imap import Source as ImapSource

  # Create a multipart email with both text and HTML
  msg = EmailMessage()
  msg.set_content("This is plain text")
  msg.add_alternative("<html><body>This is HTML</body></html>", subtype="html")

  # Extract with HTML only
  body_text, body_html = ImapSource._get_email_body(msg, body_types="html")

  assert body_text is None
  assert body_html is not None
  assert body_html.strip() == "<html><body>This is HTML</body></html>"


def test_body_types_both():
  """Test that body_types='both' extracts both text and HTML bodies."""
  from extensions.mail.imap import Source as ImapSource

  # Create a multipart email with both text and HTML
  msg = EmailMessage()
  msg.set_content("This is plain text")
  msg.add_alternative("<html><body>This is HTML</body></html>", subtype="html")

  # Extract both
  body_text, body_html = ImapSource._get_email_body(msg, body_types="both")

  assert body_text is not None
  assert body_html is not None
  assert body_text.strip() == "This is plain text"
  assert body_html.strip() == "<html><body>This is HTML</body></html>"


def test_email_address_normalization():
  """Test that email addresses are normalized to lowercase."""
  email_addr = EmailAddress(email="Test@Example.COM", name="Test User")

  # Email should be normalized to lowercase
  assert email_addr.email == "test@example.com"
  assert email_addr.name == "Test User"


def test_email_address_resolver_get_text_with_name():
  """Test EmailAddressResolver.get_text() with name."""
  from extensions.mail.resolver import EmailAddressResolver
  from app.schemas.info_base.block import BlockModel

  email_block_data = EmailAddress(email="test@example.com", name="Test User")

  block = BlockModel(
    resolver="email_address",
    content=email_block_data.model_dump_json(),
  )

  resolver = EmailAddressResolver(block)

  # Should return name and email in angle brackets format
  text = asyncio.run(resolver.get_text())
  assert text == "Test User <test@example.com>"


def test_email_address_resolver_get_text_without_name():
  """Test EmailAddressResolver.get_text() without name."""
  from extensions.mail.resolver import EmailAddressResolver
  from app.schemas.info_base.block import BlockModel

  email_block_data = EmailAddress(email="test@example.com", name=None)

  block = BlockModel(
    resolver="email_address",
    content=email_block_data.model_dump_json(),
  )

  resolver = EmailAddressResolver(block)

  # Should return just the email
  text = asyncio.run(resolver.get_text())
  assert text == "test@example.com"


def test_email_address_resolver_embedding_string():
  """Test EmailAddressResolver.get_str_for_embedding()."""
  from extensions.mail.resolver import EmailAddressResolver
  from app.schemas.info_base.block import BlockModel

  email_block_data = EmailAddress(email="test@example.com", name="Test User")

  block = BlockModel(
    resolver="email_address",
    content=email_block_data.model_dump_json(),
  )

  resolver = EmailAddressResolver(block)

  # Should return name and email for embedding
  embedding_str = asyncio.run(resolver.get_str_for_embedding())
  assert embedding_str == "Test User test@example.com"
