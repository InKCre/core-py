"""Tests for telegram extension."""

import sys
import os

# Set a dummy database connection string to avoid engine creation error
os.environ.setdefault("DB_CONN_STRING", "sqlite:///:memory:")

from extensions.telegram.schema import TelegramMessage, TelegramUser, TelegramChat
from datetime import datetime


def test_telegram_user_schema():
    """Test Telegram user schema."""
    user = TelegramUser(
        id=12345,
        first_name="John",
        last_name="Doe",
        username="johndoe",
        is_bot=False
    )
    
    assert user.id == 12345
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert user.username == "johndoe"
    assert user.is_bot is False
    
    # Test without optional fields
    user2 = TelegramUser(id=67890, first_name="Jane")
    assert user2.last_name is None
    assert user2.username is None


def test_telegram_chat_schema():
    """Test Telegram chat schema."""
    chat = TelegramChat(
        id=123456,
        type="private",
        username="johndoe"
    )
    
    assert chat.id == 123456
    assert chat.type == "private"
    assert chat.username == "johndoe"
    
    # Test group chat
    group_chat = TelegramChat(
        id=789012,
        type="group",
        title="Test Group"
    )
    assert group_chat.title == "Test Group"


def test_telegram_message_schema():
    """Test Telegram message schema creation."""
    user = TelegramUser(
        id=12345,
        first_name="John",
        username="johndoe"
    )
    
    chat = TelegramChat(
        id=123456,
        type="private"
    )
    
    message = TelegramMessage(
        message_id=100,
        date=datetime(2024, 1, 1, 12, 0, 0),
        chat=chat,
        from_user=user,
        text="Hello from Telegram!",
        has_media=False
    )
    
    assert message.message_id == 100
    assert message.text == "Hello from Telegram!"
    assert message.from_user.username == "johndoe"
    assert message.chat.type == "private"
    assert message.has_media is False


def test_telegram_message_with_media():
    """Test Telegram message with media."""
    user = TelegramUser(id=12345, first_name="John")
    chat = TelegramChat(id=123456, type="private")
    
    message = TelegramMessage(
        message_id=101,
        date=datetime(2024, 1, 1, 12, 0, 0),
        chat=chat,
        from_user=user,
        caption="Check out this photo!",
        has_media=True,
        media_type="photo"
    )
    
    assert message.has_media is True
    assert message.media_type == "photo"
    assert message.caption == "Check out this photo!"


def test_telegram_message_serialization():
    """Test message serialization to JSON and back."""
    user = TelegramUser(id=12345, first_name="John")
    chat = TelegramChat(id=123456, type="private")
    
    original_message = TelegramMessage(
        message_id=100,
        date=datetime(2024, 1, 1, 12, 0, 0),
        chat=chat,
        from_user=user,
        text="Test message"
    )
    
    # Serialize to JSON
    json_str = original_message.model_dump_json()
    
    # Deserialize from JSON
    restored_message = TelegramMessage.model_validate_json(json_str)
    
    assert restored_message.message_id == original_message.message_id
    assert restored_message.text == original_message.text
    assert restored_message.from_user.id == original_message.from_user.id
