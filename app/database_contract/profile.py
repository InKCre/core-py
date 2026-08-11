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
class StorageTypeProfile:
  id: str
  description: str
  config_schema: JsonObject
  writable: bool


@dataclass(frozen=True)
class SourceTypeProfile:
  id: str
  description: str
  config_schema: JsonObject
  collect_config_schema: JsonObject
  backfill_config_schema: JsonObject | None = None


@dataclass(frozen=True)
class JobTypeProfile:
  id: str
  description: str
  parameters_schema: JsonObject
  default_timeout_seconds: int


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
  StorageTypeProfile(
    "http",
    "HTTP storage for bounded retrieval of opaque response bytes.",
    HTTP_STORAGE_SCHEMA,
    False,
  ),
)

BUILTIN_STORAGE_TYPES += (
  StorageTypeProfile(
    "postgresql_binary",
    "PostgreSQL storage for deployment-owned binary content.",
    _object_schema(
      "PostgreSQLBinaryStorageConfig",
      "Configuration for PostgreSQL binary storage.",
      {},
    ),
    True,
  ),
)


SOURCE_COLLECT_PARAMETERS_SCHEMA = {
  "additionalProperties": False,
  "description": "Parameters of the exact ordinary Source Job type.",
  "properties": {
    "config": {
      "additionalProperties": True,
      "title": "Config",
      "type": "object",
    },
    "source": {"title": "Source", "type": "integer"},
  },
  "required": ["source"],
  "title": "SourceCollectParameters",
  "type": "object",
}

SOURCE_BACKFILL_PARAMETERS_SCHEMA = {
  **SOURCE_COLLECT_PARAMETERS_SCHEMA,
  "description": "Parameters of the exact historical Source Job type.",
  "title": "SourceBackfillParameters",
}

BUILTIN_JOB_TYPES = (
  JobTypeProfile(
    "core.source.collect.v1",
    "Run one ordinary collection command for a configured Source.",
    SOURCE_COLLECT_PARAMETERS_SCHEMA,
    300,
  ),
  JobTypeProfile(
    "core.source.backfill.v1",
    "Run one exact historical collection command for a configured Source.",
    SOURCE_BACKFILL_PARAMETERS_SCHEMA,
    1800,
  ),
)


EMPTY_SOURCE_COMMAND_SCHEMA = {
  "additionalProperties": False,
  "properties": {},
  "title": "EmptySourceCommandConfig",
  "type": "object",
}

GITHUB_COLLECT_SCHEMA = {
  "additionalProperties": False,
  "properties": {"full": _boolean(False)},
  "title": "CollectConfig",
  "type": "object",
}

TWITTER_COLLECT_SCHEMA = {
  "additionalProperties": False,
  "properties": {
    "full": _boolean(False),
    "result_limit": {"default": 40, "maximum": 100, "minimum": 5, "type": "integer"},
  },
  "title": "CollectConfig",
  "type": "object",
}

FEED_COLLECT_SCHEMA = {
  "additionalProperties": False,
  "description": "Per-run overrides admitted by the RSS collection command.",
  "properties": {
    "download_enclosures": {
      "anyOf": [{"type": "boolean"}, {"type": "null"}],
      "default": None,
      "title": "Download Enclosures",
    },
    "fetch_full_text": {
      "anyOf": [{"type": "boolean"}, {"type": "null"}],
      "default": None,
      "title": "Fetch Full Text",
    },
    "target_storage_id": {
      "anyOf": [{"type": "integer"}, {"type": "null"}],
      "default": None,
      "title": "Target Storage Id",
    },
  },
  "title": "FeedCollectJobConfig",
  "type": "object",
}

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


MAIL_SOURCE_SCHEMA = {
  "additionalProperties": False,
  "description": "Configuration for one Mail access context.",
  "properties": {
    "protocol": {"const": "imap", "default": "imap", "type": "string"},
    "parameters": {
      "additionalProperties": False,
      "properties": {
        "host": {"minLength": 1, "type": "string"},
        "port": {"default": 993, "maximum": 65535, "minimum": 1, "type": "integer"},
        "security": {
          "default": "tls",
          "enum": ["tls", "starttls", "plain"],
          "type": "string",
        },
        "username": {"minLength": 1, "type": "string"},
        "password": {"minLength": 1, "type": "string"},
      },
      "required": ["host", "username", "password"],
      "title": "IMAPParameters",
      "type": "object",
    },
    "excluded_mailboxes": {
      "anyOf": [
        {
          "additionalProperties": False,
          "properties": {
            "names": {
              "items": {"type": "string"},
              "title": "Names",
              "type": "array",
            },
            "special_uses": {
              "items": {"type": "string"},
              "title": "Special Uses",
              "type": "array",
            },
          },
          "title": "MailboxExclusionPolicy",
          "type": "object",
        },
        {"type": "null"},
      ],
      "default": None,
    },
    "ordinary_mark_as_seen": _boolean(True),
    "backfill_mark_as_seen": _boolean(False),
    "synchronize_deletions": _boolean(False),
  },
  "required": ["parameters"],
  "title": "MailSourceConfig",
  "type": "object",
}

MAIL_BACKFILL_SCHEMA = {
  "additionalProperties": False,
  "description": "One exact historical Mail collection range.",
  "properties": {
    "since": {"format": "date", "title": "Since", "type": "string"},
    "before": {
      "anyOf": [{"format": "date", "type": "string"}, {"type": "null"}],
      "default": None,
      "title": "Before",
    },
  },
  "required": ["since"],
  "title": "MailBackfillConfig",
  "type": "object",
}


BUILTIN_SOURCE_TYPES = (
  SourceTypeProfile(
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
    GITHUB_COLLECT_SCHEMA,
  ),
  SourceTypeProfile(
    "extensions.mail.source.Source",
    "Mail Source - incrementally collects communication records through IMAP.",
    MAIL_SOURCE_SCHEMA,
    EMPTY_SOURCE_COMMAND_SCHEMA,
    MAIL_BACKFILL_SCHEMA,
  ),
  SourceTypeProfile(
    "extensions.rss.atom.Source",
    "Atom Feed Source.",
    _feed_source_schema(
      "AtomSourceConfig",
      "Configuration for Atom feed source.",
    ),
    FEED_COLLECT_SCHEMA,
  ),
  SourceTypeProfile(
    "extensions.rss.rss.Source",
    "RSS 2.0 Feed Source.",
    _feed_source_schema(
      "RssSourceConfig",
      "Configuration for RSS 2.0 source.",
    ),
    FEED_COLLECT_SCHEMA,
  ),
  SourceTypeProfile(
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
    EMPTY_SOURCE_COMMAND_SCHEMA,
  ),
  SourceTypeProfile(
    "extensions.twitter.bookmark.Source",
    "Twitter Bookmark as Source",
    _object_schema(
      "SourceConfig",
      "Configuration for Twitter Bookmark Source.",
      {},
    ),
    TWITTER_COLLECT_SCHEMA,
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
BUILTIN_JOB_TYPES_BY_ID = {item.id: item for item in BUILTIN_JOB_TYPES}
