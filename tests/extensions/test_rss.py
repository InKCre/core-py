"""Tests for RSS/Atom extension."""

import os
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

# Set required environment variables before any app imports
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing")

# Initialize logger before importing extensions
from libs.obsrv.main import setup_obsrv

setup_obsrv()

from extensions.rss.schema import FeedItem
from extensions.rss.resolver import FeedItemResolver
from app.schemas.info_base.block import BlockModel


# =============================================================================
# FeedItem Schema Tests
# =============================================================================


def test_feed_item_schema_minimal():
  """Test FeedItem schema with minimal required fields."""
  item = FeedItem(
    id="item-1",
    title="Test Article",
    link="https://example.com/article",
    content="This is the content.",
  )

  assert item.id == "item-1"
  assert item.title == "Test Article"
  assert item.link == "https://example.com/article"
  assert item.content == "This is the content."
  assert item.published is None
  assert item.author is None
  assert item.categories == ()
  assert item.enclosures == ()
  assert item.content_fetched is False


def test_feed_item_schema_full():
  """Test FeedItem schema with all fields."""
  pub_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
  upd_date = datetime(2024, 1, 16, 14, 30, 0, tzinfo=timezone.utc)

  item = FeedItem(
    id="item-2",
    title="Full Article",
    link="https://example.com/full-article",
    content="Full content here.",
    published=pub_date,
    updated=upd_date,
    author="John Doe",
    summary="A short summary.",
    feed_url="https://example.com/feed.xml",
    feed_title="Example Feed",
    categories=("tech", "news"),
    enclosures=("https://example.com/image.jpg",),
    content_fetched=True,
  )

  assert item.id == "item-2"
  assert item.published == pub_date
  assert item.updated == upd_date
  assert item.author == "John Doe"
  assert item.summary == "A short summary."
  assert item.feed_url == "https://example.com/feed.xml"
  assert item.feed_title == "Example Feed"
  assert item.categories == ("tech", "news")
  assert item.enclosures == ("https://example.com/image.jpg",)
  assert item.content_fetched is True


def test_feed_item_serialization():
  """Test FeedItem JSON serialization and deserialization."""
  item = FeedItem(
    id="item-3",
    title="Serialization Test",
    link="https://example.com/serialize",
    content="Content to serialize.",
    published=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
    categories=("test",),
  )

  json_str = item.model_dump_json()
  assert json_str is not None
  assert isinstance(json_str, str)

  restored = FeedItem.model_validate_json(json_str)
  assert restored.id == item.id
  assert restored.title == item.title
  assert restored.content == item.content
  assert restored.categories == item.categories


# =============================================================================
# FeedItemResolver Tests
# =============================================================================


def test_feed_item_resolver_create_block():
  """Test FeedItemResolver.create_block()."""
  item = FeedItem(
    id="resolver-test-1",
    title="Resolver Test",
    link="https://example.com/resolver",
    content="Resolver content.",
  )

  block = FeedItemResolver.create_block(item)

  assert block.resolver == "feed_item"
  assert block.content is not None

  # Verify content can be parsed back
  parsed = FeedItem.model_validate_json(block.content)
  assert parsed.id == item.id


def test_feed_item_resolver_create_graph():
  """Test FeedItemResolver.create_graph()."""
  item = FeedItem(
    id="graph-test-1",
    title="Graph Test",
    link="https://example.com/graph",
    content="Graph content.",
  )

  graph = FeedItemResolver.create_graph(item)

  assert graph.block.resolver == "feed_item"
  assert graph.out_arcs == ()


def test_feed_item_resolver_get_text():
  """Test FeedItemResolver.get_text()."""
  item = FeedItem(
    id="text-test-1",
    title="Text Test",
    link="https://example.com/text",
    content="This is the main content.",
    summary="This is the summary.",
  )

  block = BlockModel(
    resolver="feed_item",
    content=item.model_dump_json(),
  )

  resolver = FeedItemResolver(block)
  text = asyncio.run(resolver.get_text())

  # Should return content first
  assert text == "This is the main content."


def test_feed_item_resolver_get_text_fallback_summary():
  """Test FeedItemResolver.get_text() falls back to summary."""
  item = FeedItem(
    id="text-test-2",
    title="Text Test Fallback",
    link="https://example.com/text2",
    content="",  # Empty content
    summary="Fallback summary.",
  )

  block = BlockModel(
    resolver="feed_item",
    content=item.model_dump_json(),
  )

  resolver = FeedItemResolver(block)
  text = asyncio.run(resolver.get_text())

  assert text == "Fallback summary."


def test_feed_item_resolver_get_text_fallback_title():
  """Test FeedItemResolver.get_text() falls back to title."""
  item = FeedItem(
    id="text-test-3",
    title="Title Only",
    link="https://example.com/text3",
    content="",
    summary=None,
  )

  block = BlockModel(
    resolver="feed_item",
    content=item.model_dump_json(),
  )

  resolver = FeedItemResolver(block)
  text = asyncio.run(resolver.get_text())

  assert text == "Title Only"


def test_feed_item_resolver_get_str_for_embedding():
  """Test FeedItemResolver.get_str_for_embedding()."""
  item = FeedItem(
    id="embed-test-1",
    title="Embedding Test",
    link="https://example.com/embed",
    content="Full content for embedding.",
    summary="Summary for embedding.",
  )

  block = BlockModel(
    resolver="feed_item",
    content=item.model_dump_json(),
  )

  resolver = FeedItemResolver(block)
  embedding_str = asyncio.run(resolver.get_str_for_embedding())

  assert "Title: Embedding Test" in embedding_str
  assert "Summary: Summary for embedding." in embedding_str
  assert "Content: Full content for embedding." in embedding_str


# =============================================================================
# RSS Source Tests
# =============================================================================


RSS_FEED_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Test RSS Feed</title>
    <link>https://example.com</link>
    <description>A test feed</description>
    <item>
      <guid>item-1</guid>
      <title>First Article</title>
      <link>https://example.com/article-1</link>
      <description>Short description of article 1.</description>
      <pubDate>Mon, 15 Jan 2024 12:00:00 +0000</pubDate>
      <author>author@example.com</author>
      <category>News</category>
    </item>
    <item>
      <guid>item-2</guid>
      <title>Second Article with content:encoded</title>
      <link>https://example.com/article-2</link>
      <description>Short desc</description>
      <content:encoded><![CDATA[
        <p>This is the full content with HTML.</p>
      ]]></content:encoded>
      <pubDate>Tue, 16 Jan 2024 14:30:00 +0000</pubDate>
    </item>
    <item>
      <guid>item-3</guid>
      <title>Article with enclosure</title>
      <link>https://example.com/article-3</link>
      <description>Article with podcast attachment.</description>
      <enclosure url="https://example.com/podcast.mp3" type="audio/mpeg" length="12345678"/>
    </item>
  </channel>
</rss>"""


def test_rss_source_is_content_truncated_with_content_encoded():
  """Content is complete when content:encoded is long enough."""
  from extensions.rss.rss import Source as RssSource

  source = RssSource.__new__(RssSource)

  # content_encoded must be > 100 chars to be considered complete
  long_content = "<p>" + "This is the full article content. " * 5 + "</p>"

  result = source._is_content_truncated(
    content_encoded=long_content,
    description="Short",
    summary=None,
    content=None,
    min_length=500,
  )

  assert result is False


def test_rss_source_is_content_truncated_long_description():
  """Test _is_content_truncated returns False when description is long enough."""
  from extensions.rss.rss import Source as RssSource

  source = RssSource.__new__(RssSource)

  long_desc = "A" * 600  # 600 chars > 500 min_length

  result = source._is_content_truncated(
    content_encoded=None,
    description=long_desc,
    summary=None,
    content=None,
    min_length=500,
  )

  assert result is False


def test_rss_source_is_content_truncated_short_description():
  """Test _is_content_truncated returns True when description is too short."""
  from extensions.rss.rss import Source as RssSource

  source = RssSource.__new__(RssSource)

  result = source._is_content_truncated(
    content_encoded=None,
    description="Short description",
    summary=None,
    content=None,
    min_length=500,
  )

  assert result is True


def test_rss_source_is_content_truncated_no_content():
  """Test _is_content_truncated returns True when no content at all."""
  from extensions.rss.rss import Source as RssSource

  source = RssSource.__new__(RssSource)

  result = source._is_content_truncated(
    content_encoded=None,
    description=None,
    summary=None,
    content=None,
    min_length=500,
  )

  assert result is True


def test_rss_source_config_defaults():
  """Test RssSourceConfig has correct defaults."""
  from extensions.rss.rss import RssSourceConfig

  config = RssSourceConfig()

  assert config.feed_url == ""
  assert config.min_description_length == 500
  assert config.fetch_timeout == 30
  assert "Mozilla" in config.user_agent


# =============================================================================
# Atom Source Tests
# =============================================================================


ATOM_FEED_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test Atom Feed</title>
  <link href="https://example.com"/>
  <id>https://example.com/feed</id>
  <updated>2024-01-16T14:30:00Z</updated>
  <entry>
    <id>entry-1</id>
    <title>First Entry</title>
    <link href="https://example.com/entry-1" rel="alternate"/>
    <summary>Summary of entry 1.</summary>
    <published>2024-01-15T12:00:00Z</published>
    <updated>2024-01-15T12:00:00Z</updated>
    <author>
      <name>John Doe</name>
    </author>
    <category term="Technology"/>
  </entry>
  <entry>
    <id>entry-2</id>
    <title>Entry with full content</title>
    <link href="https://example.com/entry-2"/>
    <summary>Short summary</summary>
    <content type="html"><![CDATA[<p>Full HTML content here.</p>]]></content>
    <published>2024-01-16T14:30:00Z</published>
  </entry>
  <entry>
    <id>entry-3</id>
    <title>Entry with enclosure</title>
    <link href="https://example.com/entry-3"/>
    <link href="https://example.com/image.jpg" rel="enclosure" type="image/jpeg"/>
    <summary>Entry with image attachment.</summary>
  </entry>
</feed>"""


def test_atom_source_is_content_truncated_with_summary_and_content():
  """Test _is_content_truncated returns False when both summary and content exist."""
  from extensions.rss.atom import Source as AtomSource

  source = AtomSource.__new__(AtomSource)

  result = source._is_content_truncated(
    content_encoded=None,
    description=None,
    summary="A summary",
    content="Full content",
    min_length=500,
  )

  assert result is False


def test_atom_source_is_content_truncated_long_content():
  """Test _is_content_truncated returns False when content alone is long enough."""
  from extensions.rss.atom import Source as AtomSource

  source = AtomSource.__new__(AtomSource)

  long_content = "B" * 600

  result = source._is_content_truncated(
    content_encoded=None,
    description=None,
    summary=None,
    content=long_content,
    min_length=500,
  )

  assert result is False


def test_atom_source_is_content_truncated_short_summary_only():
  """Test _is_content_truncated returns True when only short summary exists."""
  from extensions.rss.atom import Source as AtomSource

  source = AtomSource.__new__(AtomSource)

  result = source._is_content_truncated(
    content_encoded=None,
    description=None,
    summary="Short summary",
    content=None,
    min_length=500,
  )

  assert result is True


def test_atom_source_config_defaults():
  """Test AtomSourceConfig has correct defaults."""
  from extensions.rss.atom import AtomSourceConfig

  config = AtomSourceConfig()

  assert config.feed_url == ""
  assert config.min_description_length == 500
  assert config.fetch_timeout == 30
  assert "Mozilla" in config.user_agent


# =============================================================================
# Integration-style tests with mocked HTTP
# =============================================================================


@pytest.fixture
def mock_aiohttp_session():
  """Create a mock aiohttp session."""
  mock_response = AsyncMock()
  mock_response.raise_for_status = MagicMock()
  mock_response.text = AsyncMock(return_value=RSS_FEED_SAMPLE)

  mock_session = AsyncMock()
  mock_session.get = MagicMock(
    return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
  )

  return mock_session


def test_rss_parsing_extracts_items():
  """Test that RSS feed parsing extracts correct items."""
  from bs4 import BeautifulSoup

  soup = BeautifulSoup(RSS_FEED_SAMPLE, "xml")

  channel = soup.find("channel")
  assert channel is not None

  title_elem = channel.find("title", recursive=False)
  assert title_elem is not None
  assert title_elem.get_text(strip=True) == "Test RSS Feed"

  items = soup.find_all("item")
  assert len(items) == 3

  # Check first item
  first_item = items[0]
  guid = first_item.find("guid")
  title = first_item.find("title")
  assert guid is not None
  assert title is not None
  assert guid.get_text(strip=True) == "item-1"
  assert title.get_text(strip=True) == "First Article"

  # Check content:encoded in second item
  second_item = items[1]
  content_encoded = second_item.find("content:encoded") or second_item.find("encoded")
  assert content_encoded is not None
  assert "full content" in content_encoded.get_text()

  # Check enclosure in third item
  third_item = items[2]
  enclosure = third_item.find("enclosure")
  assert enclosure is not None
  assert enclosure.get("url") == "https://example.com/podcast.mp3"


def test_atom_parsing_extracts_entries():
  """Test that Atom feed parsing extracts correct entries."""
  from bs4 import BeautifulSoup

  soup = BeautifulSoup(ATOM_FEED_SAMPLE, "xml")

  feed = soup.find("feed")
  assert feed is not None

  title_elem = feed.find("title", recursive=False)
  assert title_elem is not None
  assert title_elem.get_text(strip=True) == "Test Atom Feed"

  entries = soup.find_all("entry")
  assert len(entries) == 3

  # Check first entry
  first_entry = entries[0]
  entry_id = first_entry.find("id")
  title = first_entry.find("title")
  assert entry_id is not None
  assert title is not None
  assert entry_id.get_text(strip=True) == "entry-1"
  assert title.get_text(strip=True) == "First Entry"

  author = first_entry.find("author")
  assert author is not None
  author_name = author.find("name")
  assert author_name is not None
  assert author_name.get_text(strip=True) == "John Doe"

  # Check content in second entry
  second_entry = entries[1]
  content = second_entry.find("content")
  assert content is not None
  assert "Full HTML content" in content.get_text()

  # Check enclosure link in third entry
  third_entry = entries[2]
  enclosure_link = None
  for link in third_entry.find_all("link"):
    if link.get("rel") == "enclosure":
      enclosure_link = link
      break
  assert enclosure_link is not None
  assert enclosure_link.get("href") == "https://example.com/image.jpg"


def test_rss_pubdate_parsing():
  """Test RSS pubDate parsing."""
  from email.utils import parsedate_to_datetime

  pub_date_str = "Mon, 15 Jan 2024 12:00:00 +0000"
  parsed = parsedate_to_datetime(pub_date_str)

  assert parsed.year == 2024
  assert parsed.month == 1
  assert parsed.day == 15
  assert parsed.hour == 12


def test_atom_datetime_parsing():
  """Test Atom ISO datetime parsing."""
  date_str = "2024-01-15T12:00:00Z"
  parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

  assert parsed.year == 2024
  assert parsed.month == 1
  assert parsed.day == 15
  assert parsed.hour == 12
