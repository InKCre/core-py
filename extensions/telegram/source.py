"""Telegram Source for collecting messages sent to the bot."""

import asyncio
import typing
from typing import Optional as Opt
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from app.business.source import SourceBase
from app.schemas.root import StarGraphForm
from app.schemas.block import BlockModel, BlockID
from extensions.telegram import Extension
from .schema import TelegramMessage, TelegramUser, TelegramChat


class Source(SourceBase):
    """Telegram Source - collects messages sent to the configured Telegram bot."""

    _app: Opt[Application] = None
    _collected_messages: list[TelegramMessage] = []
    _collecting: bool = False

    @classmethod
    async def _message_handler(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming Telegram messages.
        
        This is called by the Telegram bot when a message is received.
        """
        if not update.message or not cls._collecting:
            return
        
        message = update.message
        
        # Parse user information
        from_user = None
        if message.from_user:
            from_user = TelegramUser(
                id=message.from_user.id,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                username=message.from_user.username,
                is_bot=message.from_user.is_bot
            )
        
        # Parse chat information
        chat = TelegramChat(
            id=message.chat.id,
            type=message.chat.type,
            title=message.chat.title,
            username=message.chat.username
        )
        
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
        
        # Parse forward information
        forward_from = None
        if message.forward_from:
            forward_from = TelegramUser(
                id=message.forward_from.id,
                first_name=message.forward_from.first_name,
                last_name=message.forward_from.last_name,
                username=message.forward_from.username,
                is_bot=message.forward_from.is_bot
            )
        
        # Create TelegramMessage object
        telegram_msg = TelegramMessage(
            message_id=message.message_id,
            date=message.date,
            chat=chat,
            from_user=from_user,
            text=message.text,
            caption=caption,
            forward_from=forward_from,
            reply_to_message_id=(
                message.reply_to_message.message_id if message.reply_to_message else None
            ),
            has_media=has_media,
            media_type=media_type
        )
        
        # Store the message
        cls._collected_messages.append(telegram_msg)
        
        # Update last message ID in state
        Extension.state.last_message_id = message.message_id

    async def _collect(  # type: ignore[override]
        self, full: bool = False
    ) -> typing.AsyncGenerator[StarGraphForm, None]:
        """Collect messages from Telegram bot.
        
        :param full: If True, collect all messages (not supported for Telegram bot),
                     otherwise only new messages received during collection period.
        
        Note: Telegram bots can only receive new messages sent to them in real-time.
        Historical messages cannot be retrieved via Bot API. For full collection,
        the bot needs to have been running and storing messages previously.
        """
        config = Extension.config
        
        if not config.bot_token:
            # No bot token configured, cannot collect
            return
        
        # Initialize Telegram bot application if not already done
        if Source._app is None:
            Source._app = Application.builder().token(config.bot_token).build()
            
            # Add message handler
            Source._app.add_handler(MessageHandler(filters.ALL, Source._message_handler))
        
        # Clear collected messages and start collecting
        Source._collected_messages = []
        Source._collecting = True
        
        try:
            # Start the bot in polling mode
            await Source._app.initialize()
            await Source._app.start()
            await Source._app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=not full
            )
            
            # Collect for the configured duration
            collection_duration = config.collection_duration_seconds or 60
            await asyncio.sleep(collection_duration)
            
            # Stop collecting
            Source._collecting = False
            await Source._app.updater.stop()
            await Source._app.stop()
            
            # Yield collected messages as StarGraphForm
            for message in Source._collected_messages:
                yield StarGraphForm(
                    block=BlockModel(
                        resolver="extensions.telegram.resolver.TelegramMessageResolver",
                        content=message.model_dump_json(),
                    ),
                    out_relations=()
                )
        
        finally:
            Source._collecting = False
            # Clean up
            if Source._app is not None:
                try:
                    if Source._app.running:
                        await Source._app.updater.stop()
                        await Source._app.stop()
                    await Source._app.shutdown()
                except Exception:
                    pass

    async def _organize(self, block_id: BlockID) -> None:
        """Organize collected Telegram message block.
        
        Currently no additional organization needed for Telegram messages.
        """
        pass
