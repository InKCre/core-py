"""RSS/Atom Feed Item Schema"""

__all__ = [
  "FeedItem",
]

import sqlmodel
from datetime import datetime
from typing import Optional as Opt


class FeedItem(sqlmodel.SQLModel):
  """Unified feed item model for both RSS and Atom feeds.

  This model represents a single item/entry from an RSS 2.0 or Atom feed.
  """

  id: str
  """Unique identifier for the item (guid in RSS, id in Atom)"""

  title: str
  """Title of the item"""

  link: str
  """URL to the full content"""

  content: str
  """The main content (content:encoded, description, or fetched content)"""

  published: Opt[datetime] = None
  """Publication date"""

  updated: Opt[datetime] = None
  """Last update date (mainly for Atom)"""

  author: Opt[str] = None
  """Author name"""

  summary: Opt[str] = None
  """Short summary/description"""

  feed_url: str = ""
  """The source feed URL this item came from"""

  feed_title: Opt[str] = None
  """Title of the source feed"""

  categories: tuple[str, ...] = ()
  """Categories/tags for the item"""

  enclosures: tuple[str, ...] = ()
  """Media enclosure URLs (podcasts, images, etc.)"""

  content_fetched: bool = False
  """Whether the content was fetched from the link (vs from feed)"""
