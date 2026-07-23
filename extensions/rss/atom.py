"""Atom Feed Source for collecting feed entries."""

import asyncio
import aiohttp
import html2text
import sqlmodel
from datetime import datetime
from typing import Optional as Opt
from bs4 import BeautifulSoup

from app.business.source import SourceBase
from app.business.info_base.main import InfoBaseManager
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockID
from app.schemas.info_base.main import SubGraphForm
from app.schemas.source import SourceCollectJobModel
from libs.obsrv.main import get_logger

from .schema import FeedItem
from .resolver import FeedItemResolver

LOGGER = get_logger().getChild(__name__)

DEFAULT_USER_AGENT = (
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class AtomSourceConfig(sqlmodel.SQLModel):
  """Configuration for Atom feed source."""

  feed_url: str = ""
  """The URL of the Atom feed to collect from"""

  min_description_length: int = 500
  """Minimum length of summary/content to consider as 'long enough' (not truncated)"""

  fetch_timeout: int = 30
  """Timeout in seconds for fetching content"""

  user_agent: str = DEFAULT_USER_AGENT
  """User agent string for HTTP requests"""


class Source(SourceBase[AtomSourceConfig], config_cls=AtomSourceConfig):
  """Atom Feed Source.

  Collects entries from an Atom feed URL. If the feed content appears
  truncated (no content, short summary), it will fetch the full content
  from the entry's link.
  """

  async def collect(self, job: SourceCollectJobModel) -> None:
    """Collect Atom feed entries."""
    logger = LOGGER.getChild(f"collect.{job.id}")
    config = self.get_config()
    job_config = job.config or {}
    full = job_config.get("full", False)

    if not config.feed_url:
      logger.error("No feed_url configured")
      return

    logger.info(
      "Starting Atom collection",
      extra={
        "job_id": job.id,
        "source": job.source,
        "full": full,
        "feed_url": config.feed_url,
      },
    )

    collected: list[SubGraphForm] = []
    state = self.get_state()
    seen_ids: set[str] = set(state.get("seen_ids", []))

    try:
      async with aiohttp.ClientSession(
        headers={"User-Agent": config.user_agent},
        timeout=aiohttp.ClientTimeout(total=config.fetch_timeout),
      ) as session:
        # Fetch feed
        async with session.get(config.feed_url) as response:
          response.raise_for_status()
          feed_xml = await response.text()

        logger.info("Fetched feed successfully")

        # Parse feed
        soup = BeautifulSoup(feed_xml, "xml")

        # Get feed title
        feed = soup.find("feed")
        feed_title = None
        if feed:
          title_elem = feed.find("title", recursive=False)
          if title_elem:
            feed_title = title_elem.get_text(strip=True)

        entries = soup.find_all("entry")
        logger.info(f"Found {len(entries)} entries in feed")

        for entry in entries:
          # Get entry ID
          id_elem = entry.find("id")
          item_id = id_elem.get_text(strip=True) if id_elem else ""

          if not item_id:
            logger.debug("Skipping entry without ID")
            continue

          # Skip already seen entries (unless full refresh)
          if not full and item_id in seen_ids:
            logger.debug(f"Skipping already seen entry: {item_id}")
            continue

          # Get link (prefer alternate, then self)
          link = ""
          for link_elem in entry.find_all("link"):
            rel = link_elem.get("rel", "alternate")
            if rel == "alternate" or not link:
              href = link_elem.get("href")
              if href:
                link = href
                if rel == "alternate":
                  break

          # Get title
          title_elem = entry.find("title")
          title = title_elem.get_text(strip=True) if title_elem else ""

          # Get summary
          summary_elem = entry.find("summary")
          summary = summary_elem.get_text(strip=True) if summary_elem else None

          # Get content
          content_elem = entry.find("content")
          content = None
          if content_elem:
            content = content_elem.get_text(strip=True)

          # Get published
          published_elem = entry.find("published")
          published = None
          if published_elem:
            try:
              published = datetime.fromisoformat(
                published_elem.get_text(strip=True).replace("Z", "+00:00")
              )
            except Exception:
              pass

          # Get updated
          updated_elem = entry.find("updated")
          updated = None
          if updated_elem:
            try:
              updated = datetime.fromisoformat(
                updated_elem.get_text(strip=True).replace("Z", "+00:00")
              )
            except Exception:
              pass

          # Get author
          author_elem = entry.find("author")
          author = None
          if author_elem:
            name_elem = author_elem.find("name")
            if name_elem:
              author = name_elem.get_text(strip=True)

          # Get categories
          categories = []
          for cat in entry.find_all("category"):
            term = cat.get("term") or cat.get("label")
            if term:
              categories.append(term)

          # Get enclosures (links with rel="enclosure")
          enclosures = []
          for link_elem in entry.find_all("link"):
            if link_elem.get("rel") == "enclosure":
              href = link_elem.get("href")
              if href:
                enclosures.append(href)

          # Determine content - check if truncated
          final_content = content or summary or ""
          content_fetched = False

          if self._is_content_truncated(
            None, None, summary, content, config.min_description_length
          ):
            # Try to fetch full content from link
            if link:
              logger.debug(f"Fetching full content from: {link}")
              fetched = await self._fetch_article_content(session, link, logger)
              if fetched:
                final_content = fetched
                content_fetched = True
              await asyncio.sleep(1)  # Be nice to servers

          # Create FeedItem
          feed_item = FeedItem(
            id=item_id,
            title=title,
            link=link,
            content=final_content,
            published=published,
            updated=updated,
            author=author,
            summary=summary,
            feed_url=config.feed_url,
            feed_title=feed_title,
            categories=tuple(categories),
            enclosures=tuple(enclosures),
            content_fetched=content_fetched,
          )

          collected.append(FeedItemResolver.create_graph(feed_item))
          seen_ids.add(item_id)

          logger.debug(
            "Collected feed entry",
            extra={"item_id": item_id, "title": title, "content_fetched": content_fetched},
          )

    except Exception as e:
      logger.error(
        "Failed to collect Atom feed",
        extra={"feed_url": config.feed_url, "error": str(e)},
        exc_info=True,
      )
      raise

    # Save to database
    logger.info(f"Saving {len(collected)} entries to database")
    try:
      with SessionLocal() as db:
        for graph in reversed(collected) if full else collected:
          await InfoBaseManager.add_subgraph_to_session(graph, db)
        db.commit()

      # Update state with seen IDs (keep last 1000 to avoid unbounded growth)
      state["seen_ids"] = list(seen_ids)[-1000:]
      self.set_state(state)

      logger.info(
        "Atom collection completed",
        extra={"job_id": job.id, "entries_collected": len(collected)},
      )
    except Exception as e:
      logger.error(
        "Failed to save entries to database",
        extra={"job_id": job.id, "error": str(e)},
        exc_info=True,
      )
      raise

  async def _organize(self, block_id: BlockID) -> None:
    """Organize collected feed entry block.

    Currently no additional organization needed.
    """
    pass

  def _is_content_truncated(
    self,
    content_encoded: Opt[str],
    description: Opt[str],
    summary: Opt[str],
    content: Opt[str],
    min_length: int = 500,
  ) -> bool:
    """Check if the feed content appears to be truncated.

    Returns False (not truncated) if any of:
    - has content:encoded (RSS)
    - description is long enough (RSS)
    - has both summary and content (Atom)
    - content alone is long enough
    """
    if content_encoded and len(content_encoded.strip()) > 100:
      return False

    if description and len(description.strip()) >= min_length:
      return False

    if summary and content:
      return False

    if content and len(content.strip()) >= min_length:
      return False

    return True

  async def _fetch_article_content(
    self,
    session: aiohttp.ClientSession,
    url: str,
    logger,
  ) -> Opt[str]:
    """Fetch and extract article content from a URL using readability.

    Falls back to simple HTML text extraction if readability fails.
    """
    try:
      async with session.get(url) as response:
        response.raise_for_status()
        html = await response.text()

      # Try using readability-lxml
      try:
        from readability import Document

        doc = Document(html)
        content_html = doc.summary()
        # Convert to plain text with html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        return h.handle(content_html)
      except ImportError:
        logger.debug("readability-lxml not available, using fallback")
        # Fallback to BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "header", "footer"]):
          element.decompose()

        # Try to find main content
        main = (
          soup.find("article")
          or soup.find("main")
          or soup.find(class_="content")
          or soup.find(class_="post")
          or soup.find(id="content")
          or soup.body
        )

        if main:
          h = html2text.HTML2Text()
          h.ignore_links = False
          return h.handle(str(main))

        return None
    except Exception as e:
      logger.warning(f"Failed to fetch article content from {url}: {e}")
      return None
