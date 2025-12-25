# Telegram Extension for InKCre

This extension provides Telegram bot message source functionality for InKCre.

## Features

- Collect messages sent to a configured Telegram bot
- Support for text messages, media messages (photos, videos, documents, etc.), and captions
- Track message metadata (sender, chat, timestamps)
- Support for forwarded messages and replies
- Automatic tracking of processed messages

### Message Types Supported

- Text messages
- Photos (with captions)
- Videos (with captions)
- Documents (with captions)
- Audio messages
- Voice messages
- Stickers
- Forwarded messages
- Reply messages

## Usage

### 1. Create a Telegram Bot

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow the instructions
3. Copy the bot token provided by BotFather

### 2. Install

Install the extension into `extensions/` and restart the core-py

### 3. Create a Telegram Source

Create source which type is `extensions.telegram.source.Source` in `sources` table with following values:

- `config`: A dict
  - `bot_token`: Telegram Bot API token (obtain from [@BotFather](https://t.me/botfather))
  - `passive`: Whether to register a handler to FastAPI router so that once you sent messages to the Telegram Bot, we will collect the messages immediately. (You will have to configure it following <https://core.telegram.org/bots/api#getting-updates>)
- `auto_collect`: set to a Dict follows CollectAt if you want to enable the system to run the collection intervally, instead, set to null.

### 4. Start Collecting Messages

And now your messages sent to the bot will be automatically collected to the info-base.

All collected messages will be stored as `telegram message` type block

## Notes

- The Telegram Bot API only allows bots to receive messages sent to them in real-time
- Historical messages cannot be retrieved via the Bot API (over 24 hours)
- The bot needs appropriate permissions in group chats to receive messages
- For private chats, users must start the conversation with the bot first