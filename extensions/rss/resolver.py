"""Exact use-time projections for feed, item, and enclosure metadata blocks."""

from __future__ import annotations

from lxml import html as lxml_html

from app.business.info_base.block import BlockManager
from app.business.info_base.resolver import Resolver, ResolverManager
from app.business.info_base.resolver.label import format_label
from app.schemas.info_base.block import BlockForm
from app.schemas.info_base.main import StarsGraphForm

from .repository import (
  CONTENT_RELATION,
  ENCLOSURE_RELATION,
  ENCLOSURE_RESOLVER_ID,
  FEED_ITEM_RESOLVER_ID,
  FEED_RELATION,
  FEED_RESOLVER_ID,
  FULL_TEXT_RELATION,
  FeedGraphIntegrityError,
)
from .schema import (
  CanonicalEnclosure,
  CanonicalFeed,
  CanonicalFeedItem,
  SolvedEnclosure,
  SolvedFeedItem,
)


def _plain_text(value: str | None, media_type: str | None = None) -> str | None:
  if value is None:
    return None
  normalized = value.strip()
  if not normalized:
    return None
  if media_type and "html" in media_type.lower() or normalized.startswith("<"):
    try:
      rendered = lxml_html.fromstring(normalized).text_content().strip()
      return rendered or None
    except (ValueError, TypeError):
      pass
  return normalized


class FeedResolver(Resolver[CanonicalFeed, str], rso_type=FEED_RESOLVER_ID):
  """Resolve canonical feed metadata."""

  def __post_init__(self, raw_content: str | None = None) -> None:
    if raw_content is not None:
      self.set_solved_content(CanonicalFeed.model_validate_json(raw_content))

  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> CanonicalFeed:
    del materialize_missing
    return CanonicalFeed.model_validate_json(await self.get_raw_content(refresh=refresh))

  @classmethod
  def create_block(cls, content: CanonicalFeed, storage=None) -> BlockForm:
    return BlockForm(
      resolver=cls.__rsotype__,
      content=content.model_dump_json(),
      storage=storage,
    )

  @classmethod
  def create_graph(cls, content: CanonicalFeed) -> StarsGraphForm:
    return StarsGraphForm(block=cls.create_block(content))

  async def get_text(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str | None:
    feed = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    parts = [part for part in (feed.title, feed.description) if part]
    return "\n\n".join(parts) or None

  async def get_label(self, *, refresh: bool = False) -> str:
    feed = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=False,
    )
    return format_label("feed", feed.title or feed.configured_url)


class FeedItemResolver(
  Resolver[SolvedFeedItem, str],
  rso_type=FEED_ITEM_RESOLVER_ID,
):
  """Resolve an item root with feed, enclosure, and full-text graph references."""

  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> SolvedFeedItem:
    root = CanonicalFeedItem.model_validate_json(
      await self.get_raw_content(refresh=refresh)
    )
    relations = await self.get_relations(
      include_in=False,
      include_out=True,
      refresh=refresh,
    )
    feed_ids = [r.to_ for r in relations if r.content == FEED_RELATION]
    enclosure_ids = [r.to_ for r in relations if r.content == ENCLOSURE_RELATION]
    full_text_ids = [r.to_ for r in relations if r.content == FULL_TEXT_RELATION]
    if len(feed_ids) > 1 or len(full_text_ids) > 1:
      raise FeedGraphIntegrityError(
        f"feed item {self.block_id} has ambiguous graph-owned projections"
      )
    full_text_block_id = full_text_ids[0] if full_text_ids else None
    if full_text_block_id is None and materialize_missing:
      from .enrichment import FullTextEnrichmentService

      materialized = await FullTextEnrichmentService.materialize(
        self.block_id,
        require_enabled=True,
      )
      full_text_block_id = materialized.content_block_id
    return SolvedFeedItem(
      root=root,
      feed_block_id=feed_ids[0] if feed_ids else None,
      enclosure_block_ids=tuple(enclosure_ids),
      full_text_block_id=full_text_block_id,
    )

  @classmethod
  def create_block(cls, content: CanonicalFeedItem, storage=None) -> BlockForm:
    return BlockForm(
      resolver=cls.__rsotype__,
      content=content.model_dump_json(),
      storage=storage,
    )

  @classmethod
  def create_graph(cls, content: CanonicalFeedItem) -> StarsGraphForm:
    return StarsGraphForm(block=cls.create_block(content))

  async def _full_text(
    self,
    solved: SolvedFeedItem,
    *,
    refresh: bool,
    materialize_missing: bool,
  ) -> str | None:
    if solved.full_text_block_id is None:
      return None
    block = BlockManager.get(solved.full_text_block_id)
    if block is None:
      raise FeedGraphIntegrityError(
        f"full_text relation from item {self.block_id} targets a missing block"
      )
    return await ResolverManager.get(block).get_text(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )

  async def get_text(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str | None:
    solved = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    full_text = await self._full_text(
      solved,
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    parts = [
      _plain_text(solved.root.title),
      _plain_text(solved.root.summary, "text/html"),
      full_text
      or _plain_text(solved.root.authored_content, solved.root.authored_content_type),
    ]
    return "\n\n".join(part for part in parts if part) or None

  async def get_label(self, *, refresh: bool = False) -> str:
    root = CanonicalFeedItem.model_validate_json(
      await self.get_raw_content(refresh=refresh)
    )
    identifier = (
      root.title
      or root.source_native_id
      or root.alternate_url
      or _plain_text(root.authored_content, root.authored_content_type)
    )
    return format_label("feed item", identifier, first_line=True)


class EnclosureResolver(
  Resolver[SolvedEnclosure, str],
  rso_type=ENCLOSURE_RESOLVER_ID,
):
  """Resolve protocol metadata and an optional materialized semantic child."""

  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> SolvedEnclosure:
    del materialize_missing
    root = CanonicalEnclosure.model_validate_json(
      await self.get_raw_content(refresh=refresh)
    )
    relations = await self.get_relations(
      include_in=False,
      include_out=True,
      refresh=refresh,
    )
    content_ids = [
      relation.to_ for relation in relations if relation.content == CONTENT_RELATION
    ]
    if len(content_ids) > 1:
      raise FeedGraphIntegrityError(
        f"enclosure {self.block_id} has more than one semantic content child"
      )
    return SolvedEnclosure(
      root=root,
      content_block_id=content_ids[0] if content_ids else None,
    )

  @classmethod
  def create_block(cls, content: CanonicalEnclosure, storage=None) -> BlockForm:
    return BlockForm(
      resolver=cls.__rsotype__,
      content=content.model_dump_json(),
      storage=storage,
    )

  @classmethod
  def create_graph(cls, content: CanonicalEnclosure) -> StarsGraphForm:
    return StarsGraphForm(block=cls.create_block(content))

  async def get_text(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str | None:
    solved = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    return solved.root.title

  async def get_label(self, *, refresh: bool = False) -> str:
    root = CanonicalEnclosure.model_validate_json(
      await self.get_raw_content(refresh=refresh)
    )
    return format_label("feed enclosure", root.title or root.url)

  async def materialize_content(self, *, target_storage_id: int):
    """Execute the enclosure-specific lazy materialization command."""
    from .enrichment import EnclosureMaterializationService

    return await EnclosureMaterializationService.materialize(
      self.block_id,
      target_storage_id=target_storage_id,
    )


__all__ = ["EnclosureResolver", "FeedItemResolver", "FeedResolver"]
