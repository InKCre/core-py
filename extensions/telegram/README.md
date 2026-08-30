# Telegram Extension

Telegram is a private delivery inbox for saving useful content to InKCre. Send or forward a message directly to the configured bot; the bot does not join or collect the originating chat.

## Source configuration

Create one Source of type `extensions.telegram.source.Source` with:

- `bot_token`: token issued by [@BotFather](https://t.me/botfather)
- `bound_user_id`: the one numeric Telegram user ID admitted by this Source
- `download_attachments`: optional, defaults to `false`

Use one bot identity for at most one Telegram Source because Telegram exposes one update queue per bot. This MVP documents that operator constraint but does not add cross-Source enforcement or pairing UI.

Run collection through the ordinary `core.source.collect.v1` Job, manually or from a user-configured Cron. The Extension does not create a schedule. Telegram retains unconfirmed updates for a limited time, so collection frequency is an operator choice.

## Saved content

- authored or forwarded text becomes ordinary `core.text.v1` or `core.html.v1` content;
- supported files become `extensions.telegram.attachment.v1` metadata, with captions as related ordinary text/HTML;
- with the default `download_attachments=false`, no bytes are downloaded;
- `POST /telegram/attachments/materialize` explicitly downloads one attachment into the Source's writable Storage; setting `download_attachments=true` invokes the same operation after metadata is committed.

Successfully committed messages receive a 👍 reaction. The bot replies only for `/start`, unsupported content, partial attachment materialization, or retryable failure. Existing `extensions.telegram.message.v1` Blocks from version `0.1.0` remain readable, but new collection does not create them.

Groups, channels, chat history, pairing, setup UI, edited messages, album reconstruction, OCR, and automatic scheduling are outside this MVP.
