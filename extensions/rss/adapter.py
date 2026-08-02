"""feedparser adapter from protocol-native documents to canonical feed facts."""

from __future__ import annotations

import calendar
import dataclasses
import datetime
import typing
from urllib.parse import urljoin

import feedparser
import pydantic

from .schema import (
  CanonicalEnclosure,
  CanonicalFeed,
  CanonicalFeedItem,
  FeedAuthor,
  FeedFamily,
  ParsedFeedItem,
  ParsedFeedSnapshot,
)


class UnsupportedFeedFamilyError(ValueError):
  """The parsed document is not the protocol family configured by the source."""


class UnusableFeedDocumentError(ValueError):
  """feedparser could not produce a usable feed document."""


@dataclasses.dataclass(frozen=True)
class FeedParserContext:
  expected_family: FeedFamily
  source_instance_id: int
  configured_url: str
  effective_url: str
  response_headers: dict[str, str]


def _text(value: object) -> str | None:
  if value is None:
    return None
  normalized = str(value).strip()
  return normalized or None


def _datetime_from_parsed(value: object) -> datetime.datetime | None:
  if value is None:
    return None
  try:
    timestamp = calendar.timegm(typing.cast(tuple[int, ...], value))
  except (TypeError, ValueError, OverflowError):
    return None
  return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)


def _links(value: object) -> tuple[dict[str, object], ...]:
  if not isinstance(value, (list, tuple)):
    return ()
  return tuple(dict(link) for link in value if isinstance(link, dict))


def _link_by_rel(value: object, rel: str, base_url: str) -> str | None:
  for link in _links(value):
    if _text(link.get("rel")) == rel:
      href = _text(link.get("href"))
      return urljoin(base_url, href) if href is not None else None
  return None


def _authors(value: object) -> tuple[FeedAuthor, ...]:
  if not isinstance(value, (list, tuple)):
    return ()
  authors: list[FeedAuthor] = []
  for raw_author in value:
    if not isinstance(raw_author, dict):
      continue
    author = FeedAuthor(
      name=_text(raw_author.get("name")),
      email=_text(raw_author.get("email")),
      url=_text(raw_author.get("href")),
    )
    if author.name or author.email or author.url:
      authors.append(author)
  return tuple(authors)


def _categories(value: object) -> tuple[str, ...]:
  if not isinstance(value, (list, tuple)):
    return ()
  categories: list[str] = []
  for raw_category in value:
    if not isinstance(raw_category, dict):
      continue
    category = _text(raw_category.get("term") or raw_category.get("label"))
    if category and category not in categories:
      categories.append(category)
  return tuple(categories)


def _enclosures(
  links: object,
  family: FeedFamily,
  diagnostics: list[dict[str, object]],
  item_index: int,
  base_url: str,
) -> tuple[CanonicalEnclosure, ...]:
  enclosures: list[CanonicalEnclosure] = []
  for raw_link in _links(links):
    if _text(raw_link.get("rel")) != "enclosure":
      continue
    raw_url = _text(raw_link.get("href"))
    if raw_url is None:
      diagnostics.append(
        {
          "scope": "enclosure",
          "code": "missing_url",
          "item_index": item_index,
        }
      )
      continue
    url = urljoin(base_url, raw_url)
    length = None
    raw_length = _text(raw_link.get("length"))
    if raw_length is not None:
      try:
        length = int(raw_length)
      except ValueError:
        diagnostics.append(
          {
            "scope": "enclosure",
            "code": "invalid_declared_length",
            "item_index": item_index,
            "url": url,
          }
        )
    try:
      enclosures.append(
        CanonicalEnclosure(
          family=family,
          url=url,
          declared_media_type=_text(raw_link.get("type")),
          declared_length=length,
          title=_text(raw_link.get("title")),
        )
      )
    except pydantic.ValidationError as error:
      diagnostics.append(
        {
          "scope": "enclosure",
          "code": "invalid_metadata",
          "item_index": item_index,
          "message": str(error),
        }
      )
  return tuple(enclosures)


def _feed_family(version: str) -> FeedFamily | None:
  normalized = version.lower()
  if normalized.startswith("rss"):
    return "rss"
  if normalized.startswith("atom"):
    return "atom"
  return None


def parse_feed_snapshot(
  body: bytes,
  context: FeedParserContext,
) -> ParsedFeedSnapshot:
  """Parse a complete bounded response without performing network I/O."""
  parser_headers = {key.lower(): value for key, value in context.response_headers.items()}
  parser_headers["content-location"] = context.effective_url
  parsed = feedparser.parse(body, response_headers=parser_headers)
  parsed_family = _feed_family(_text(parsed.get("version")) or "")
  if parsed_family != context.expected_family:
    raise UnsupportedFeedFamilyError(
      f"expected {context.expected_family}, parsed {parsed_family or 'unknown'} feed family"
    )
  family: FeedFamily = context.expected_family
  if not parsed.get("feed"):
    raise UnusableFeedDocumentError("feed document has no usable feed metadata")

  feed_data = dict(typing.cast(dict[str, object], parsed.feed))
  feed = CanonicalFeed(
    source_instance_id=context.source_instance_id,
    family=family,
    configured_url=context.configured_url,
    source_native_id=_text(feed_data.get("id")),
    declared_self_url=_link_by_rel(feed_data.get("links"), "self", context.effective_url),
    title=_text(feed_data.get("title")),
    home_url=_link_by_rel(feed_data.get("links"), "alternate", context.effective_url)
    or _text(feed_data.get("link")),
    description=_text(feed_data.get("subtitle") or feed_data.get("description")),
    language=_text(feed_data.get("language")),
    authored_updated_at=_datetime_from_parsed(feed_data.get("updated_parsed")),
  )

  diagnostics: list[dict[str, object]] = []
  if bool(parsed.get("bozo")):
    diagnostics.append(
      {
        "scope": "feed",
        "code": "parse_warning",
        "message": str(parsed.get("bozo_exception") or "feedparser reported bozo"),
      }
    )

  items: list[ParsedFeedItem] = []
  for index, raw_entry in enumerate(parsed.entries):
    entry = dict(typing.cast(dict[str, object], raw_entry))
    try:
      source_native_id = _text(entry.get("id"))
      alternate_url = _link_by_rel(entry.get("links"), "alternate", context.effective_url)
      contents = entry.get("content")
      authored_content = None
      authored_content_type = None
      if isinstance(contents, (list, tuple)) and contents:
        first_content = contents[0]
        if isinstance(first_content, dict):
          authored_content = _text(first_content.get("value"))
          authored_content_type = _text(first_content.get("type"))

      item = CanonicalFeedItem(
        source_native_id=source_native_id,
        source_native_id_kind=("atom_id" if family == "atom" else "rss_guid")
        if source_native_id is not None
        else None,
        alternate_url=alternate_url,
        title=_text(entry.get("title")),
        summary=_text(entry.get("summary")),
        authored_content=authored_content,
        authored_content_type=authored_content_type,
        authored_published_at=_datetime_from_parsed(entry.get("published_parsed")),
        authored_updated_at=_datetime_from_parsed(entry.get("updated_parsed")),
        authors=_authors(entry.get("authors")),
        categories=_categories(entry.get("tags")),
      )
      items.append(
        ParsedFeedItem(
          item=item,
          enclosures=_enclosures(
            entry.get("links"),
            family,
            diagnostics,
            index,
            context.effective_url,
          ),
        )
      )
    except (pydantic.ValidationError, ValueError) as error:
      diagnostics.append(
        {
          "scope": "item",
          "code": "malformed_item",
          "item_index": index,
          "message": str(error),
        }
      )

  return ParsedFeedSnapshot(
    feed=feed,
    items=tuple(items),
    diagnostics=tuple(diagnostics),
  )


__all__ = [
  "FeedParserContext",
  "UnsupportedFeedFamilyError",
  "UnusableFeedDocumentError",
  "parse_feed_snapshot",
]
