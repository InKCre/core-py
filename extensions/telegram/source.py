"""Telegram Source for collecting messages sent to the bot."""

import asyncio
import typing
from typing import Optional as Opt, Literal as Lit
import sqlmodel
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from app.business.source import SourceBase
from app.engine import SessionLocal
from app.business.info_base.root import RootManager
from app.schemas.info_base.main import StarGraphForm
from app.schemas.info_base.block import BlockModel, BlockID
from app.schemas.source import SourceCollectJobModel
from app.scheduler import scheduler
from .schema import TelegramMessage


class SourceConfig(sqlmodel.SQLModel):
  """Configuration of Telegram Source."""

  bot_token: str = ""
  """Telegram Bot API token (get from @BotFather)"""
  collect_method: Lit["polling", "webhook"] = "polling"
  """Method to collect messages: 'polling' (getUpdates) or 'webhook'"""
  collection_duration_seconds: int = 60
  """Duration in seconds to collect messages during each polling collection run (default: 60)"""
  webhook_url: str = ""
  """Webhook URL for receiving updates (required when collect_method is 'webhook')"""


class Source(SourceBase[SourceConfig], config_cls=SourceConfig):
  """Telegram Source - collects messages sent to the configured Telegram bot.
  
  Supports two collection methods:
  1. Polling (getUpdates): Actively fetches updates from Telegram servers
  2. Webhook: Receives updates via HTTP POST requests to configured webhook URL

  Note: This source uses class-level state for the Telegram application and message
  collection. Only one collection run should be active at a time. Running multiple
  concurrent collections may cause race conditions.
  """

  _app: Opt[Application] = None
  _collected_messages: list[TelegramMessage] = []
  _collecting: bool = False

  @classmethod
  async def _message_handler(
    cls, update: Update, context: ContextTypes.DEFAULT_TYPE
  ) -> None:
    """Handle incoming Telegram messages.

    This is called by the Telegram bot when a message is received.
    """
    if not update.message or not cls._collecting:
      return

    message = update.message

    # Determine media type
    has_media = False
    media_type = None
    caption = None

    if message.photo:
      has_media = True
      media_type = "photo"
      caption = message.caption
    elif message.video:
      has_media = True
      media_type = "video"
      caption = message.caption
    elif message.document:
      has_media = True
      media_type = "document"
      caption = message.caption
    elif message.audio:
      has_media = True
      media_type = "audio"
      caption = message.caption
    elif message.voice:
      has_media = True
      media_type = "voice"
      caption = message.caption
    elif message.sticker:
      has_media = True
      media_type = "sticker"

    # Create TelegramMessage object with only message data
    telegram_msg = TelegramMessage(
      message_id=message.message_id,
      date=message.date,
      text=message.text,
      caption=caption,
      reply_to_message_id=(
        message.reply_to_message.message_id if message.reply_to_message else None
      ),
      has_media=has_media,
      media_type=media_type,
    )

    # Store the message
    cls._collected_messages.append(telegram_msg)

  async def collect(self, job: SourceCollectJobModel) -> None:
    """Collect messages from Telegram bot.

    :param job: The collect job containing config and state.

    Supports two collection methods:
    - polling: Uses getUpdates to fetch messages for a specified duration
    - webhook: Sets up webhook endpoint (webhook must be configured separately)

    Note: Telegram bots can only receive new messages sent to them in real-time.
    Historical messages cannot be retrieved via Bot API. For full collection,
    the bot needs to have been running and storing messages previously.
    """
    config = self.get_config()

    if not config.bot_token:
      # No bot token configured, cannot collect
      return

    job_config = job.config or {}
    full = job_config.get("full", False)

    # Dispatch to appropriate collection method
    if config.collect_method == "webhook":
      await self._collect_webhook(config, full)
    else:  # Default to polling
      await self._collect_polling(config, full, job_config)

  async def _collect_polling(
    self, config: SourceConfig, full: bool, job_config: dict
  ) -> None:
    """Collect messages using polling (getUpdates) method.
    
    :param config: Source configuration
    :param full: Whether to fetch all pending updates
    :param job_config: Job-specific configuration
    """
    duration = job_config.get(
      "duration", config.collection_duration_seconds or 60
    )

    # Initialize Telegram bot application if not already done
    if Source._app is None:
      Source._app = Application.builder().token(config.bot_token).build()

      # Add message handler
      Source._app.add_handler(MessageHandler(filters.ALL, Source._message_handler))

    # Clear collected messages and start collecting
    Source._collected_messages = []
    Source._collecting = True

    collected = []
    try:
      # Start the bot in polling mode
      await Source._app.initialize()
      await Source._app.start()
      await Source._app.updater.start_polling(
        allowed_updates=Update.ALL_TYPES, drop_pending_updates=not full
      )

      # Collect for the configured duration
      await asyncio.sleep(duration)

      # Stop collecting
      Source._collecting = False
      await Source._app.updater.stop()
      await Source._app.stop()

      # Collect messages as StarGraphForm
      for message in Source._collected_messages:
        collected.append(
          StarGraphForm(
            block=BlockModel(
              resolver="extensions.telegram.resolver.TelegramMessageResolver",
              content=message.model_dump_json(),
            ),
            out_relations=(),
          )
        )

      # Update last message ID in state after successful collection
      if Source._collected_messages:
        state = self.get_state()
        state["last_message_id"] = Source._collected_messages[-1].message_id
        self.set_state(state)

    finally:
      Source._collecting = False
      # Clean up
      if Source._app is not None:
        try:
          if Source._app.running:
            await Source._app.updater.stop()
            await Source._app.stop()
          await Source._app.shutdown()
        except (RuntimeError, TimeoutError) as e:
          # Expected errors during cleanup can be safely ignored
          pass

    with SessionLocal() as db:
      for graph in collected:
        RootManager.add_star_graph_to_session(graph, db)
        # Schedule organize
        scheduler.add_job(
          func=self._organize,
          kwargs={"block_id": graph.block.id},
          misfire_grace_time=None,
        )
      db.commit()

  async def _collect_webhook(self, config: SourceConfig, full: bool) -> None:
    """Collect messages using webhook method.
    
    Note: Webhook collection requires external webhook setup.
    This method is a placeholder for webhook-based collection.
    The actual webhook endpoint should be configured separately using
    Telegram's setWebhook API and a web server to receive updates.
    
    :param config: Source configuration
    :param full: Whether to process all pending updates (not applicable for webhooks)
    """
    # Webhook collection is handled by external webhook endpoint
    # This method exists as placeholder for future webhook implementation
    # For now, webhook messages should be processed through a separate endpoint
    # that calls _message_handler directly
    pass

  async def _organize(self, block_id: BlockID) -> None:
    """Organize collected Telegram message block.

    Currently no additional organization needed for Telegram messages.
    """
    pass
