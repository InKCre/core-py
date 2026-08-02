"""RSS/Atom Feed Extension for InKCre.

Provides RssSource and AtomSource for collecting feed items from
RSS 2.0 and Atom feeds.
"""

import sqlmodel
from fastapi import APIRouter
from app.business.extension.main import ExtensionBase


class RssExtensionConfig(sqlmodel.SQLModel):
  """Configuration for RSS extension."""

  ...


class Extension(
  ExtensionBase[RssExtensionConfig],
  ext_id="rss",
  config_cls=RssExtensionConfig,
):
  """RSS/Atom Feed Extension.

  This extension provides two source types:
  - RssSource: For RSS 2.0 feeds
  - AtomSource: For Atom feeds

  Each source instance collects items from a single feed URL.
  Content is fetched from the item link if the feed appears truncated
  (missing content:encoded, short description, or lacking both summary and content).
  """

  @classmethod
  def _init_resolvers(cls):
    """Initialize exact feed-family resolvers."""
    from .resolver import EnclosureResolver, FeedItemResolver, FeedResolver  # noqa: F401

  @classmethod
  def _init_sources(cls):
    """Initialize RSS and Atom sources."""
    from .rss import Source as RssSource  # noqa: F401
    from .atom import Source as AtomSource  # noqa: F401

  @classmethod
  def _register_apis(cls, router: APIRouter):
    """Register API endpoints for RSS extension."""
    from .api import register_api

    register_api(router)
