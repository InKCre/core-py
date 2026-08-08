"""Checked-in built-in catalog profile.

The profile is data only. Reconciliation can consume it without importing FastAPI,
application settings, extension runtimes, or the scheduler.
"""

from dataclasses import dataclass
from typing import Any


JsonObject = dict[str, Any]


@dataclass(frozen=True)
class ExtensionProfile:
  id: str
  version: str
  nickname: str


@dataclass(frozen=True)
class TypeProfile:
  id: str
  description: str
  config_schema: JsonObject


@dataclass(frozen=True)
class StorageProfile:
  id: int
  type: str
  nickname: str
  config: JsonObject


def _object_schema(
  title: str,
  description: str,
  properties: JsonObject,
) -> JsonObject:
  return {
    "description": description,
    "properties": properties,
    "title": title,
    "type": "object",
  }


def _string(default: str = "") -> JsonObject:
  return {"default": default, "type": "string"}


def _integer(default: int) -> JsonObject:
  return {"default": default, "type": "integer"}


def _positive_integer(default: int) -> JsonObject:
  return {"default": default, "exclusiveMinimum": 0, "type": "integer"}


def _boolean(default: bool) -> JsonObject:
  return {"default": default, "type": "boolean"}


HTTP_STORAGE_SCHEMA = _object_schema(
  "HTTPStorageConfig",
  "Configuration for HTTP storage.",
  {
    "follow_redirects": _boolean(True),
    "max_response_bytes": _positive_integer(64 * 1024 * 1024),
    "timeout": _positive_integer(30),
  },
)

OPENAI_COMPATIBLE_DIALECT_SCHEMA = {
  "additionalProperties": False,
  "description": "Connection values for one OpenAI-compatible provider instance.",
  "properties": {
    "api_key": {
      "minLength": 1,
      "title": "Api Key",
      "type": "string",
    },
    "base_url": {
      "anyOf": [
        {"minLength": 1, "type": "string"},
        {"type": "null"},
      ],
      "default": None,
      "title": "Base Url",
    },
  },
  "required": ["api_key"],
  "title": "OpenAICompatibleConfig",
  "type": "object",
}

BUILTIN_AI_DIALECTS = (
  TypeProfile(
    "core.openai-compatible.v1",
    "OpenAI-compatible embedding and chat protocol.",
    OPENAI_COMPATIBLE_DIALECT_SCHEMA,
  ),
)

BUILTIN_EXTENSIONS = (
  ExtensionProfile("github", "0.1.0", "GitHub"),
  ExtensionProfile("learn_english", "0.1.0", "Learn English"),
  ExtensionProfile("mail", "0.1.0", "Mail"),
  ExtensionProfile("memos", "0.1.0", "Memos"),
  ExtensionProfile("rss", "0.1.0", "RSS/Atom Feeds"),
  ExtensionProfile("telegram", "0.1.0", "Telegram"),
  ExtensionProfile("twitter", "0.1.0", "Twitter"),
)

BUILTIN_STORAGE_TYPES = (
  TypeProfile(
    "http",
    "HTTP storage for bounded retrieval of opaque response bytes.",
    HTTP_STORAGE_SCHEMA,
  ),
)

BUILTIN_STORAGE_TYPES += (
  TypeProfile(
    "postgresql_binary",
    "PostgreSQL storage for deployment-owned binary content.",
    _object_schema(
      "PostgreSQLBinaryStorageConfig",
      "Configuration for PostgreSQL binary storage.",
      {},
    ),
  ),
)

_FEED_PROPERTIES = {
  "feed_url": {"type": "string"},
  "request_timeout_seconds": _positive_integer(30),
  "max_feed_bytes": _positive_integer(8 * 1024 * 1024),
  "fetch_full_text": _boolean(True),
  "max_article_bytes": _positive_integer(8 * 1024 * 1024),
  "download_enclosures": _boolean(False),
  "max_enclosure_bytes": _positive_integer(64 * 1024 * 1024),
  "target_storage_id": _integer(-4),
  "unidentified_item_behavior": {
    "default": "create",
    "enum": ["create", "discard"],
    "type": "string",
  },
  "user_agent": _string("InKCre RSS/0.1"),
}


def _feed_source_schema(title: str, description: str) -> JsonObject:
  schema = _object_schema(title, description, _FEED_PROPERTIES)
  schema["additionalProperties"] = False
  schema["required"] = ["feed_url"]
  return schema


BUILTIN_SOURCE_TYPES = (
  TypeProfile(
    "extensions.github.stars.Source",
    "GitHub Stars Source - collects starred repositories from GitHub.",
    _object_schema(
      "SourceConfig",
      "Configuration of GitHub Stars Source.",
      {
        "github_token": _string(),
        "include_private": _boolean(False),
        "username": _string(),
      },
    ),
  ),
  TypeProfile(
    "extensions.mail.imap.Source",
    "IMAP Source - collects emails from IMAP server.",
    _object_schema(
      "SourceConfig",
      "Configuration of IMAP Source.",
      {
        "body_types": {
          "default": "text",
          "enum": ["text", "html", "both"],
          "type": "string",
        },
        "imap_port": _integer(993),
        "imap_server": _string(),
        "mark_as_seen": _boolean(True),
        "password": _string(),
        "use_ssl": _boolean(True),
        "username": _string(),
      },
    ),
  ),
  TypeProfile(
    "extensions.mail.newsletter.Source",
    "Newsletter Source - collects newsletters from IMAP server by filtering sender.",
    _object_schema(
      "NewsletterSourceConfig",
      "Configuration of Newsletter Source.",
      {
        "imap_port": _integer(993),
        "imap_server": _string(),
        "mailbox": _string("INBOX"),
        "newsletter_name": _string(),
        "password": _string(),
        "sender_email": _string(),
        "use_ssl": _boolean(True),
        "username": _string(),
      },
    ),
  ),
  TypeProfile(
    "extensions.rss.atom.Source",
    "Atom Feed Source.",
    _feed_source_schema(
      "AtomSourceConfig",
      "Configuration for Atom feed source.",
    ),
  ),
  TypeProfile(
    "extensions.rss.rss.Source",
    "RSS 2.0 Feed Source.",
    _feed_source_schema(
      "RssSourceConfig",
      "Configuration for RSS 2.0 source.",
    ),
  ),
  TypeProfile(
    "extensions.telegram.source.Source",
    "Telegram Source - collects messages sent to the configured Telegram bot.",
    _object_schema(
      "SourceConfig",
      "Configuration of Telegram Source.",
      {
        "bot_token": _string(),
        "collect_method": {
          "default": "default",
          "enum": ["default", "webhook"],
          "type": "string",
        },
      },
    ),
  ),
  TypeProfile(
    "extensions.twitter.bookmark.Source",
    "Twitter Bookmark as Source",
    _object_schema(
      "SourceConfig",
      "Configuration for Twitter Bookmark Source.",
      {},
    ),
  ),
)

BUILTIN_STORAGES = (
  StorageProfile(-1, "http", "HTTP", {}),
  StorageProfile(-4, "postgresql_binary", "PostgreSQL Binary", {}),
)

BUILTIN_EXTENSIONS_BY_ID = {item.id: item for item in BUILTIN_EXTENSIONS}
BUILTIN_AI_DIALECTS_BY_ID = {item.id: item for item in BUILTIN_AI_DIALECTS}
BUILTIN_STORAGE_TYPES_BY_ID = {item.id: item for item in BUILTIN_STORAGE_TYPES}
BUILTIN_SOURCE_TYPES_BY_ID = {item.id: item for item in BUILTIN_SOURCE_TYPES}
