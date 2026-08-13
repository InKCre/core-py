"""Tests for telegram extension."""

import asyncio
import os

import fastapi
from fastapi.routing import APIRoute

# Set a dummy database connection string to avoid engine creation error
os.environ.setdefault("DB_CONN_STRING", "sqlite:///:memory:")

from extensions.telegram.schema import TelegramMessage
from extensions.telegram import Extension
from datetime import datetime
from app.business.source import SourceManager


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


def test_runtime_module_loads_and_registers_a_working_source_api(monkeypatch):
  router = fastapi.APIRouter()
  Extension._register_apis(router)
  route = next(
    route
    for route in router.routes
    if isinstance(route, APIRoute) and route.path == "/bot/{source_id}"
  )
  assert route.endpoint.__annotations__["source_id"] is int
  recorded: list[dict[str, object]] = []

  class FakeSource:
    async def record(self, data):
      recorded.append(data)

  monkeypatch.setattr(SourceManager, "get_source_ins", lambda source_id: FakeSource())

  class FakeRequest:
    async def json(self):
      return {"update_id": 7}

  response = asyncio.run(route.endpoint(17, FakeRequest()))
  assert response == {"ok": True}
  assert recorded == [{"update_id": 7}]
