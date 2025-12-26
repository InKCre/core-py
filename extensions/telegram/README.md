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

1. Create a Telegram Bot
  1. Message [@BotFather](https://t.me/botfather) on Telegram
  2. Send `/newbot` and follow the instructions
  3. Copy the bot token provided by BotFather
2. Install: copy source code into `extensions/` and restart the core-py, and enable
3. Create a Telegram Source:
  Create source which type is `extensions.telegram.source.Source` in `sources` table with following values:
    - `config`: A dict
      - `bot_token`: Telegram Bot API token (obtain from [@BotFather](https://t.me/botfather))
      - `collect_method`: The method to collect messages, can be `webhook` or `default`. 
    - `auto_collect`: schedule the interval collect; only available for collect_method `default`
4. Setup your bot webhook URL if `collect_method` is `webhook`. 
   The wekbook URL is `https://your.inkcre-core.tld/telegram/bot/{source_id}`.
   And you should delete the webhook URL as you delete the source.
   If you want to use `default` collect method, delete the webhook URL is the prerequisite.

And now your messages sent to the bot will be automatically collected to the info-base.

All collected messages will be stored as `telegram message` type block

## Notes

- The Telegram Bot API only allows bots to receive messages sent to them in real-time
- Historical messages cannot be retrieved via the Bot API (over 24 hours)
- The bot needs appropriate permissions in group chats to receive messages
- For private chats, users must start the conversation with the bot first