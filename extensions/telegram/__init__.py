"""Telegram extension for InKCre - provides Telegram bot message source."""

import sqlmodel
from typing import Optional as Opt
from fastapi import APIRouter
from app.business.extension import ExtensionBase
from app.business.source import SourceManager


class TelegramExtensionConfig(sqlmodel.SQLModel):
    """Configuration for Telegram extension."""
    bot_token: str = ""
    """Telegram Bot API token (get from @BotFather)"""
    collection_duration_seconds: int = 60
    """Duration in seconds to collect messages during each collection run (default: 60)"""


class TelegramExtensionState(sqlmodel.SQLModel):
    """State for Telegram extension."""
    last_message_id: Opt[int] = None
    """Last processed message ID"""


class Extension(
    ExtensionBase[TelegramExtensionConfig, TelegramExtensionState],
    ext_id="telegram",
    config_cls=TelegramExtensionConfig,
    state_cls=TelegramExtensionState,
):
    """Telegram extension - provides bot message source for collecting messages."""

    @classmethod
    def _init_resolvers(cls):
        """Initialize Telegram message resolver."""
        from .resolver import TelegramMessageResolver  # noqa: F401

    @classmethod
    def _init_sources(cls):
        """Initialize Telegram bot source."""
        from .source import Source as TelegramSource  # noqa: F401

    @classmethod
    def _register_apis(cls, router: APIRouter):
        """Register API endpoints for Telegram extension."""
        router.post("/bot")(
            lambda nickname: SourceManager.create(
                f"extensions.{cls.__extid__}.source", nickname
            )
        )
