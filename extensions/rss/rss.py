"""RSS 2.0 Feed Source for collecting feed items."""

import asyncio
import aiohttp
import html2text
import sqlmodel
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional as Opt
from bs4 import BeautifulSoup

from app.business.source import SourceBase
from app.business.info_base.root import RootManager
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockID, BlockModel
from app.schemas.info_base.main import StarGraphForm
from app.schemas.source import SourceCollectJobModel
from app.scheduler import scheduler
from libs.obsrv.main import get_logger

from .schema import FeedItem
from .resolver import FeedItemResolver

LOGGER = get_logger().getChild(__name__)

DEFAULT_USER_AGENT = (
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class RssSourceConfig(sqlmodel.SQLModel):
  """Configuration for RSS 2.0 source."""

  feed_url: str = ""
  """The URL of the RSS feed to collect from"""

  min_description_length: int = 500
  """Minimum length of description to consider as 'long enough' (not truncated)"""

  fetch_timeout: int = 30
  """Timeout in seconds for fetching content"""

  user_agent: str = DEFAULT_USER_AGENT
  """User agent string for HTTP requests"""


class Source(SourceBase[RssSourceConfig], config_cls=RssSourceConfig):
  """RSS 2.0 Feed Source.

  Collects items from an RSS 2.0 feed URL. If the feed content appears
  truncated (no content:encoded, short description), it will fetch the
  full content from the item's link.
  """

  async def collect(self, job: SourceCollectJobModel) -> None:
    """Collect RSS feed items."""
    logger = LOGGER.getChild(f"collect.{job.id}")
    config = self.get_config()
    job_config = job.config or {}
    full = job_config.get("full", False)

    if not config.feed_url:
      logger.error("No feed_url configured")
      return

    logger.info(
      "Starting RSS collection",
      extra={
        "job_id": job.id,
        "source": job.source,
        "full": full,
        "feed_url": config.feed_url,
      },
    )

    collected: list[StarGraphForm] = []
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
        channel = soup.find("channel")
        feed_title = None
        if channel:
          title_elem = channel.find("title", recursive=False)
          if title_elem:
            feed_title = title_elem.get_text(strip=True)

        items = soup.find_all("item")
        logger.info(f"Found {len(items)} items in feed")

        for item in items:
          # Get item ID (guid or link)
          guid_elem = item.find("guid")
          link_elem = item.find("link")
          item_id = ""
          if guid_elem:
            item_id = guid_elem.get_text(strip=True)
          elif link_elem:
            item_id = link_elem.get_text(strip=True)

          if not item_id:
            logger.debug("Skipping item without ID")
            continue

          # Skip already seen items (unless full refresh)
          if not full and item_id in seen_ids:
            logger.debug(f"Skipping already seen item: {item_id}")
            continue

          # Get link
          link = ""
          if link_elem:
            link = link_elem.get_text(strip=True)

          # Get title
          title_elem = item.find("title")
          title = title_elem.get_text(strip=True) if title_elem else ""

          # Get description
          desc_elem = item.find("description")
          description = desc_elem.get_text(strip=True) if desc_elem else None

          # Get content:encoded
          content_encoded_elem = item.find("content:encoded") or item.find("encoded")
          content_encoded = (
            content_encoded_elem.get_text(strip=True) if content_encoded_elem else None
          )

          # Get pubDate
          pub_date_elem = item.find("pubDate")
          published = None
          if pub_date_elem:
            try:
              published = parsedate_to_datetime(pub_date_elem.get_text(strip=True))
            except Exception:
              pass

          # Get author
          author_elem = item.find("author") or item.find("dc:creator")
          author = author_elem.get_text(strip=True) if author_elem else None

          # Get categories
          categories = [cat.get_text(strip=True) for cat in item.find_all("category")]

          # Get enclosures
          enclosures = []
          for enclosure in item.find_all("enclosure"):
            url = enclosure.get("url")
            if url:
              enclosures.append(url)

          # Determine content - check if truncated
          final_content = content_encoded or description or ""
          content_fetched = False

          if self._is_content_truncated(
            content_encoded, description, None, None, config.min_description_length
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
            updated=None,
            author=author,
            summary=description,
            feed_url=config.feed_url,
            feed_title=feed_title,
            categories=tuple(categories),
            enclosures=tuple(enclosures),
            content_fetched=content_fetched,
          )

          collected.append(FeedItemResolver.create_graph(feed_item))
          seen_ids.add(item_id)

          logger.debug(
            "Collected feed item",
            extra={"item_id": item_id, "title": title, "content_fetched": content_fetched},
          )

    except Exception as e:
      logger.error(
        "Failed to collect RSS feed",
        extra={"feed_url": config.feed_url, "error": str(e)},
        exc_info=True,
      )
      raise

    # Save to database
    logger.info(f"Saving {len(collected)} items to database")
    try:
      with SessionLocal() as db:
        for graph in reversed(collected) if full else collected:
          await RootManager.add_star_graph_to_session(graph, db)
        db.commit()

      # Update state with seen IDs (keep last 1000 to avoid unbounded growth)
      state["seen_ids"] = list(seen_ids)[-1000:]
      self.set_state(state)

      logger.info(
        "RSS collection completed",
        extra={"job_id": job.id, "items_collected": len(collected)},
      )
    except Exception as e:
      logger.error(
        "Failed to save items to database",
        extra={"job_id": job.id, "error": str(e)},
        exc_info=True,
      )
      raise

  async def _organize(self, block_id: BlockID) -> None:
    """Organize collected feed item block.

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
    - has content:encoded
    - description is long enough
    - has both summary and content
    """
    if content_encoded and len(content_encoded.strip()) > 100:
      return False

    if description and len(description.strip()) >= min_length:
      return False

    if summary and content:
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
