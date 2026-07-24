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


def _boolean(default: bool) -> JsonObject:
  return {"default": default, "type": "boolean"}


HTTP_STORAGE_SCHEMA = _object_schema(
  "HTTPStorageConfig",
  "Configuration for HTTP storage.",
  {
    "follow_redirects": _boolean(True),
    "timeout": _integer(30),
  },
)

BUILTIN_EXTENSIONS = (
  ExtensionProfile("github", "0.1.0", "GitHub"),
  ExtensionProfile("learn_english", "0.1.0", "Learn English"),
  ExtensionProfile("mail", "0.1.0", "Mail"),
  ExtensionProfile("rss", "0.1.0", "RSS/Atom Feeds"),
  ExtensionProfile("telegram", "0.1.0", "Telegram"),
  ExtensionProfile("twitter", "0.1.0", "Twitter"),
)

BUILTIN_STORAGE_TYPES = tuple(
  TypeProfile(id_, description, HTTP_STORAGE_SCHEMA)
  for id_, description in (
    (
      "http",
      "Base HTTP storage for fetching content from remote URLs.",
    ),
    ("http_binary", "HTTP storage for binary content."),
    ("http_html", "HTTP storage for HTML content."),
    ("http_image", "HTTP storage for image content."),
    ("http_json", "HTTP storage for JSON content."),
    ("http_text", "HTTP storage for plain text content."),
    ("http_video", "HTTP storage for video content."),
  )
)

_FEED_PROPERTIES = {
  "feed_url": _string(),
  "fetch_timeout": _integer(30),
  "min_description_length": _integer(500),
  "user_agent": _string(
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
  ),
}

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
    _object_schema(
      "AtomSourceConfig",
      "Configuration for Atom feed source.",
      _FEED_PROPERTIES,
    ),
  ),
  TypeProfile(
    "extensions.rss.rss.Source",
    "RSS 2.0 Feed Source.",
    _object_schema(
      "RssSourceConfig",
      "Configuration for RSS 2.0 source.",
      _FEED_PROPERTIES,
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
  StorageProfile(-1, "http_image", "HTTP Image", {}),
  StorageProfile(-2, "http_video", "HTTP Video", {}),
  StorageProfile(-3, "http_html", "HTTP HTML", {}),
)

BUILTIN_EXTENSIONS_BY_ID = {item.id: item for item in BUILTIN_EXTENSIONS}
BUILTIN_STORAGE_TYPES_BY_ID = {item.id: item for item in BUILTIN_STORAGE_TYPES}
BUILTIN_SOURCE_TYPES_BY_ID = {item.id: item for item in BUILTIN_SOURCE_TYPES}
