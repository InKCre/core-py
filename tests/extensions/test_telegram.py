"""Tests for telegram extension."""

import os

# Set a dummy database connection string to avoid engine creation error
os.environ.setdefault("DB_CONN_STRING", "sqlite:///:memory:")

from extensions.telegram.schema import TelegramMessage
from datetime import datetime


def test_telegram_message_schema():
  """Test Telegram message schema creation."""
  message = TelegramMessage(
    message_id=100,
    date=datetime(2024, 1, 1, 12, 0, 0),
    text="Hello from Telegram!",
    has_media=False,
  )

  assert message.message_id == 100
  assert message.text == "Hello from Telegram!"
  assert message.has_media is False


def test_telegram_message_with_media():
  """Test Telegram message with media."""
  message = TelegramMessage(
    message_id=101,
    date=datetime(2024, 1, 1, 12, 0, 0),
    caption="Check out this photo!",
    has_media=True,
    media_type="photo",
  )

  assert message.has_media is True
  assert message.media_type == "photo"
  assert message.caption == "Check out this photo!"


def test_telegram_message_with_reply():
  """Test Telegram message with reply."""
  message = TelegramMessage(
    message_id=102,
    date=datetime(2024, 1, 1, 12, 0, 0),
    text="This is a reply",
    reply_to_message_id=100,
    has_media=False,
  )

  assert message.reply_to_message_id == 100
  assert message.text == "This is a reply"


def test_telegram_message_serialization():
  """Test message serialization to JSON and back."""
  original_message = TelegramMessage(
    message_id=100,
    date=datetime(2024, 1, 1, 12, 0, 0),
    text="Test message",
  )

  # Serialize to JSON
  json_str = original_message.model_dump_json()

  # Deserialize from JSON
  restored_message = TelegramMessage.model_validate_json(json_str)

  assert restored_message.message_id == original_message.message_id
  assert restored_message.text == original_message.text
  assert restored_message.date == original_message.date
