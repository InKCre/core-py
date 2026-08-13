"""Canonical RSS/Atom content, source configuration, and runtime projections."""

from __future__ import annotations

import datetime
from typing import Literal
from urllib.parse import urlparse

import pydantic
import sqlmodel


FeedFamily = Literal["rss", "atom"]
NativeItemIDKind = Literal["rss_guid", "atom_id"]
UnidentifiedItemBehavior = Literal["create", "discard"]


def _require_http_url(value: str) -> str:
  value = value.strip()
  parsed = urlparse(value)
  if parsed.scheme not in {"http", "https"} or not parsed.netloc:
    raise ValueError("must be a non-empty HTTP(S) URL")
  return value


class FeedSourceConfig(sqlmodel.SQLModel):
  """Durable configuration shared by the RSS and Atom source wrappers."""

  model_config = pydantic.ConfigDict(extra="forbid")

  feed_url: str
  request_timeout_seconds: int = pydantic.Field(default=30, gt=0)
  max_feed_bytes: int = pydantic.Field(default=8 * 1024 * 1024, gt=0)
  fetch_full_text: bool = True
  max_article_bytes: int = pydantic.Field(default=8 * 1024 * 1024, gt=0)
  download_enclosures: bool = False
  max_enclosure_bytes: int = pydantic.Field(default=64 * 1024 * 1024, gt=0)
  target_storage_id: int = -4
  unidentified_item_behavior: UnidentifiedItemBehavior = "create"
  user_agent: str = "InKCre RSS/0.1"

  _validate_feed_url = pydantic.field_validator("feed_url")(_require_http_url)


class FeedCollectJobConfig(pydantic.BaseModel):
  """Per-run overrides admitted by the RSS collection command."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  fetch_full_text: bool | None = None
  download_enclosures: bool | None = None
  target_storage_id: int | None = None


class FeedSourceState(pydantic.BaseModel):
  """Long-lived conditional request and unidentified-item watermark state."""

  model_config = pydantic.ConfigDict(extra="ignore", frozen=True)

  etag: str | None = None
  last_modified: str | None = None
  last_successful_contentful_snapshot_observed_at: datetime.datetime | None = None
  snapshot_configured_url: str | None = None
  snapshot_feed_block_id: int | None = None


class CanonicalFeed(pydantic.BaseModel):
  """Feed-authored facts scoped to one configured source instance."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  source_instance_id: int
  family: FeedFamily
  configured_url: str
  source_native_id: str | None = None
  declared_self_url: str | None = None
  title: str | None = None
  home_url: str | None = None
  description: str | None = None
  language: str | None = None
  authored_updated_at: datetime.datetime | None = None

  def identity(self) -> tuple[object, ...]:
    """Return exact feed continuity evidence using the accepted ladder."""
    if self.source_native_id is not None:
      return ("source_native_id", self.source_instance_id, self.source_native_id)
    if self.declared_self_url is not None:
      return ("declared_self_url", self.source_instance_id, self.declared_self_url)
    return ("configured_url", self.source_instance_id, self.configured_url)


class FeedAuthor(pydantic.BaseModel):
  """One author assertion carried by a feed item."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  name: str | None = None
  email: str | None = None
  url: str | None = None


class CanonicalFeedItem(pydantic.BaseModel):
  """Native item facts; feed membership and derived content remain graph-owned."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  source_native_id: str | None = None
  source_native_id_kind: NativeItemIDKind | None = None
  alternate_url: str | None = None
  title: str | None = None
  summary: str | None = None
  authored_content: str | None = None
  authored_content_type: str | None = None
  authored_published_at: datetime.datetime | None = None
  authored_updated_at: datetime.datetime | None = None
  authors: tuple[FeedAuthor, ...] = ()
  categories: tuple[str, ...] = ()

  @pydantic.model_validator(mode="after")
  def validate_native_identity(self) -> "CanonicalFeedItem":
    if (self.source_native_id is None) != (self.source_native_id_kind is None):
      raise ValueError("source_native_id and source_native_id_kind must appear together")
    if not any(
      (
        self.source_native_id,
        self.alternate_url,
        self.title,
        self.summary,
        self.authored_content,
      )
    ):
      raise ValueError("feed item does not contain usable authored information")
    return self

  def identity(self) -> tuple[str, str] | None:
    """Return exact source identity using the accepted protocol ladder."""
    if self.source_native_id is not None and self.source_native_id_kind is not None:
      return (self.source_native_id_kind, self.source_native_id)
    if self.alternate_url is not None:
      return ("alternate_url", self.alternate_url)
    return None

  def source_time(self) -> datetime.datetime | None:
    """Return the best feed-authored time for watermark admission only."""
    return self.authored_updated_at or self.authored_published_at


class CanonicalEnclosure(pydantic.BaseModel):
  """Protocol-authored enclosure metadata; downloaded bytes stay graph-owned."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  family: FeedFamily
  url: str
  declared_media_type: str | None = None
  declared_length: int | None = pydantic.Field(default=None, ge=0)
  title: str | None = None

  _validate_url = pydantic.field_validator("url")(_require_http_url)


class ParsedFeedItem(pydantic.BaseModel):
  """Adapter result keeping item facts and graph-owned enclosures together in memory."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  item: CanonicalFeedItem
  enclosures: tuple[CanonicalEnclosure, ...] = ()


class ParsedFeedSnapshot(pydantic.BaseModel):
  """Bounded feedparser adapter result."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  feed: CanonicalFeed
  items: tuple[ParsedFeedItem, ...]
  diagnostics: tuple[dict[str, object], ...] = ()


class SolvedFeedItem(pydantic.BaseModel):
  """Root plus graph references needed by use-time feed item projection."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  root: CanonicalFeedItem
  feed_block_id: int | None = None
  enclosure_block_ids: tuple[int, ...] = ()
  full_text_block_id: int | None = None


class SolvedEnclosure(pydantic.BaseModel):
  """Enclosure metadata plus an optional materialized semantic content child."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  root: CanonicalEnclosure
  content_block_id: int | None = None


__all__ = [
  "CanonicalEnclosure",
  "CanonicalFeed",
  "CanonicalFeedItem",
  "FeedAuthor",
  "FeedCollectJobConfig",
  "FeedFamily",
  "FeedSourceConfig",
  "FeedSourceState",
  "NativeItemIDKind",
  "ParsedFeedItem",
  "ParsedFeedSnapshot",
  "SolvedEnclosure",
  "SolvedFeedItem",
  "UnidentifiedItemBehavior",
]
