# Telegram Extension for InKCre

This extension provides Telegram bot message source functionality for InKCre.

## Features

- Collect messages sent to a configured Telegram bot
- Support for text messages, media messages (photos, videos, documents, etc.), and captions
- Track message metadata (sender, chat, timestamps)
- Support for forwarded messages and replies
- Automatic tracking of processed messages

## Configuration

The extension requires the following configuration:

- `bot_token`: Telegram Bot API token (obtain from [@BotFather](https://t.me/botfather))
- `collection_duration_seconds`: Duration in seconds to collect messages during each collection run (default: `60`)

## Usage

### 1. Create a Telegram Bot

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow the instructions
3. Copy the bot token provided by BotFather

### 2. Install and Configure the Extension

1. Install the extension in the InKCre database
2. Configure the bot token in the extension config:
   ```json
   {
     "bot_token": "YOUR_BOT_TOKEN_HERE",
     "collection_duration_seconds": 60
   }
   ```

### 3. Create a Telegram Source

Create a Telegram bot source via the API endpoint: `POST /telegram/bot`

### 4. Start Collecting Messages

- Messages will be collected based on the configured schedule
- During collection, the bot will listen for incoming messages for the specified duration
- All messages received during that period will be stored as blocks

## How It Works

1. When a collection run starts, the bot begins polling for new messages
2. All messages sent to the bot during the collection period are captured
3. Each message is stored as a block with its full metadata
4. The extension tracks the last message ID to maintain state

## Message Types Supported

- Text messages
- Photos (with captions)
- Videos (with captions)
- Documents (with captions)
- Audio messages
- Voice messages
- Stickers
- Forwarded messages
- Reply messages

## Notes

- The Telegram Bot API only allows bots to receive messages sent to them in real-time
- Historical messages cannot be retrieved via the Bot API
- The bot needs appropriate permissions in group chats to receive messages
- For private chats, users must start the conversation with the bot first
- The `collection_duration_seconds` parameter determines how long each collection run will listen for messages
