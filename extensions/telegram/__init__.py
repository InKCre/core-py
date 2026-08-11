"""Telegram extension for InKCre - provides Telegram bot message source."""

import sqlmodel
from fastapi import APIRouter
from app.business.extension.main import ExtensionBase
from app.business.source import SourceManager
from app.schemas.source import SourceID


class TelegramExtensionConfig(sqlmodel.SQLModel):
  """Configuration for Telegram extension.

  This extension has no extension-level configuration.
  Source-specific configuration (bot_token, collect_method)
  should be set in the individual source instance configuration.
  """


class Extension(
  ExtensionBase[TelegramExtensionConfig],
  ext_id="telegram",
  config_cls=TelegramExtensionConfig,
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
    from fastapi import Request

    async def telegram_webhook(source_id: SourceID, request: Request):
      """Webhook endpoint for receiving Telegram updates.

      :param source_id: The source instance ID
      :param request: FastAPI request containing webhook payload
      """
      source = SourceManager.get_source_ins(source_id)
      data = await request.json()
      await source.record(data)
      return {"ok": True}

    router.post("/bot/{source_id}")(telegram_webhook)
