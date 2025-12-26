"""Telegram Source for collecting messages sent to the bot."""

import typing
from typing import Optional as Opt, Literal as Lit
import sqlmodel
from telegram import Update
from telegram.ext import Application
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
  collect_method: Lit["default", "webhook"] = "default"
  """Method to collect messages: 'default' (getUpdates periodically) or 'webhook'"""
  webhook_url: str = ""
  """Optional webhook URL for receiving updates. If not provided, auto-generated from settings.https_url"""


class Source(SourceBase[SourceConfig], config_cls=SourceConfig):
  """Telegram Source - collects messages sent to the configured Telegram bot.
  
  Supports two collection methods:
  1. Default (getUpdates): Periodically fetches updates via scheduled collect()
  2. Webhook: Receives updates via HTTP POST to /bot/{source_id} endpoint

  Note: Telegram message queue can hold up to 100 updates. If collect() is not
  called within 24 hours or queue exceeds 100 messages, message loss may occur.
  This is controllable by the user via the collect_at schedule configuration.
  """

  def _parse_telegram_message(self, message) -> TelegramMessage:
    """Parse Telegram message into TelegramMessage object.
    
    :param message: Telegram message object
    :return: TelegramMessage data model
    """
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
    return TelegramMessage(
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

  async def collect(self, job: SourceCollectJobModel) -> None:
    """Collect messages using getUpdates (default method).

    :param job: The collect job containing config and state.

    Fetches all pending updates from Telegram using getUpdates API.
    Should be called periodically (at least every 24 hours) to avoid message loss.
    """
    config = self.get_config()

    if not config.bot_token:
      # No bot token configured, cannot collect
      return

    # Initialize Telegram bot application
    app = Application.builder().token(config.bot_token).build()
    
    collected = []
    try:
      await app.initialize()
      
      # Get last update_id from state
      state = self.get_state()
      last_update_id = state.get("last_update_id", 0)
      
      # Fetch updates using getUpdates
      # offset = last_update_id + 1 to get only new updates
      updates = await app.bot.get_updates(
        offset=last_update_id + 1 if last_update_id else None,
        allowed_updates=Update.ALL_TYPES
      )
      
      # Process each update
      for update in updates:
        if update.message:
          telegram_msg = self._parse_telegram_message(update.message)
          
          # Create StarGraphForm
          collected.append(
            StarGraphForm(
              block=BlockModel(
                resolver="extensions.telegram.resolver.TelegramMessageResolver",
                content=telegram_msg.model_dump_json(),
              ),
              out_relations=(),
            )
          )
        
        # Update last_update_id
        if update.update_id > last_update_id:
          last_update_id = update.update_id
      
      # Save last_update_id to state
      if last_update_id > state.get("last_update_id", 0):
        state["last_update_id"] = last_update_id
        self.set_state(state)
      
    finally:
      await app.shutdown()

    # Save collected messages to database
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

  async def record(self, data: typing.Any) -> None:
    """Record message from webhook (passive collection).

    :param data: Update data from Telegram webhook (dict or Update object)
    
    This method is called when a webhook receives an update from Telegram.
    """
    # Parse the update
    if isinstance(data, dict):
      update = Update.de_json(data, None)
    else:
      update = data
    
    if not update or not update.message:
      return
    
    # Parse message
    telegram_msg = self._parse_telegram_message(update.message)
    
    # Create StarGraphForm
    graph = StarGraphForm(
      block=BlockModel(
        resolver="extensions.telegram.resolver.TelegramMessageResolver",
        content=telegram_msg.model_dump_json(),
      ),
      out_relations=(),
    )
    
    # Save to database
    with SessionLocal() as db:
      RootManager.add_star_graph_to_session(graph, db)
      # Schedule organize
      scheduler.add_job(
        func=self._organize,
        kwargs={"block_id": graph.block.id},
        misfire_grace_time=None,
      )
      db.commit()

  async def _organize(self, block_id: BlockID) -> None:
    """Organize collected Telegram message block.

    Currently no additional organization needed for Telegram messages.
    """
    pass
