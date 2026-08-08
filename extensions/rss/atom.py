"""Durable Atom source type wrapper."""

from app.business.source import SourceBase

from .schema import FeedSourceConfig
from .source import FeedSourceMixin


AtomSourceConfig = FeedSourceConfig


class Source(
  FeedSourceMixin,
  SourceBase[FeedSourceConfig],
  config_cls=FeedSourceConfig,
):
  """Collect one configured Atom feed through the shared feed service."""

  expected_family = "atom"


__all__ = ["AtomSourceConfig", "Source"]
