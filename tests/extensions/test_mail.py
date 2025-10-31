"""Tests for mail extension."""

import sys
import os

# Set a dummy database connection string to avoid engine creation error
os.environ.setdefault("DB_CONN_STRING", "sqlite:///:memory:")

from extensions.mail.schema import Email, EmailAddress
from datetime import datetime


def test_email_schema():
    """Test email schema creation."""
    email = Email(
        uid=12345,
        message_id="<test@example.com>",
        subject="Test Email",
        from_=EmailAddress(email="sender@example.com", name="Sender"),
        to=[EmailAddress(email="recipient@example.com", name="Recipient")],
        date=datetime(2024, 1, 1, 12, 0, 0),
        body_text="This is a test email.",
        has_attachments=False
    )
    
    assert email.uid == 12345
    assert email.subject == "Test Email"
    assert email.from_.email == "sender@example.com"
    assert len(email.to) == 1


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
        from_=EmailAddress(email="sender@example.com", name="Sender"),
        to=[EmailAddress(email="recipient@example.com", name="Recipient")],
        date=datetime(2024, 1, 1, 12, 0, 0),
        body_text="This is a test email.",
        has_attachments=False
    )
    
    json_str = email.model_dump_json()
    assert json_str is not None
    assert isinstance(json_str, str)
    
    # Test deserialization
    email2 = Email.model_validate_json(json_str)
    assert email2.uid == email.uid
    assert email2.subject == email.subject
