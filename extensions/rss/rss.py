"""Durable RSS 2.0 source type wrapper."""

from app.business.source import SourceBase

from .schema import FeedSourceConfig
from .source import FeedSourceMixin


RssSourceConfig = FeedSourceConfig


class Source(
  FeedSourceMixin,
  SourceBase[FeedSourceConfig],
  config_cls=FeedSourceConfig,
):
  """Collect one configured RSS 2.0 feed through the shared feed service."""

  expected_family = "rss"


__all__ = ["RssSourceConfig", "Source"]
