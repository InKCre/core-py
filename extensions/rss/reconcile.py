"""Transactional reconciliation of canonical feed graphs."""

from __future__ import annotations

import dataclasses


from app.persistence.info_base.uow import GraphUnitOfWork, graph_uow
from app.persistence.source.uow import source_uow
from app.schemas.info_base.block import BlockForm, BlockModel
from app.schemas.info_base.relation import RelationModel

from .schema import CanonicalEnclosure, CanonicalFeed, CanonicalFeedItem


FEED_RESOLVER_ID = "extensions.rss.feed.v1"
FEED_ITEM_RESOLVER_ID = "extensions.rss.feed_item.v1"
ENCLOSURE_RESOLVER_ID = "extensions.rss.enclosure.v1"

FEED_RELATION = "feed"
ENCLOSURE_RELATION = "enclosure"
FULL_TEXT_RELATION = "full_text"
CONTENT_RELATION = "content"


class FeedGraphIntegrityError(RuntimeError):
  """Persisted exact RSS graph facts are ambiguous or malformed."""


@dataclasses.dataclass(frozen=True)
class ReconcileResult:
  block_id: int
  action: str
  alternate_url_changed: bool = False


def _block_id(block: BlockModel) -> int:
  if block.id is None:
    raise RuntimeError("Persisted block is missing its database ID")
  return block.id


async def _replace_content(
  block: BlockModel,
  content: str,
  uow: GraphUnitOfWork,
) -> bool:
  if block.content == content:
    return False
  block.content = content
  await uow.blocks.save(block)
  return True


class FeedGraphReconciler:
  """Own graph reconciliation mechanics without owning source policy."""

  @classmethod
  async def reconcile_feed(cls, canonical: CanonicalFeed) -> ReconcileResult:
    async with source_uow() as source_work:
      source = await source_work.sources.get(canonical.source_instance_id, lock=True)
      if source is None:
        raise FeedGraphIntegrityError("feed Source does not exist")
      uow = source_work.graph
      matches: list[BlockModel] = []
      for block in await uow.blocks.get_by_resolvers((FEED_RESOLVER_ID,)):
        try:
          candidate = CanonicalFeed.model_validate_json(block.content)
        except ValueError as error:
          raise FeedGraphIntegrityError(
            f"feed block {block.id} has invalid canonical content"
          ) from error
        if candidate.identity() == canonical.identity():
          matches.append(block)
      if len(matches) > 1:
        raise FeedGraphIntegrityError(
          f"feed identity {canonical.identity()!r} has multiple exact roots"
        )

      content = canonical.model_dump_json()
      if matches:
        feed = matches[0]
        changed = await _replace_content(feed, content, uow)
        result = ReconcileResult(_block_id(feed), "updated" if changed else "unchanged")
      else:
        feed = await uow.blocks.create(
          BlockForm(resolver=FEED_RESOLVER_ID, content=content),
        )
        result = ReconcileResult(_block_id(feed), "created")
      return result

  @classmethod
  async def _item_roots(
    cls,
    feed_block_id: int,
    uow: GraphUnitOfWork,
  ) -> tuple[tuple[BlockModel, CanonicalFeedItem], ...]:
    relations = await uow.relations.get(
      feed_block_id, include_out=False, content=FEED_RELATION
    )
    blocks = {
      block.id: block
      for block in await uow.blocks.get_many(tuple(r.from_ for r in relations))
    }
    roots: list[tuple[BlockModel, CanonicalFeedItem]] = []
    for relation in relations:
      block = blocks.get(relation.from_)
      if block is None or block.resolver != FEED_ITEM_RESOLVER_ID:
        raise FeedGraphIntegrityError(
          f"feed relation {relation.id} does not originate at an exact item root"
        )
      try:
        canonical = CanonicalFeedItem.model_validate_json(block.content)
      except ValueError as error:
        raise FeedGraphIntegrityError(
          f"feed item block {block.id} has invalid canonical content"
        ) from error
      roots.append((block, canonical))
    return tuple(roots)

  @classmethod
  async def _find_item(
    cls,
    feed_block_id: int,
    canonical: CanonicalFeedItem,
    uow: GraphUnitOfWork,
  ) -> BlockModel | None:
    identity = canonical.identity()
    if identity is None:
      return None
    matches = [
      block
      for block, persisted in await cls._item_roots(feed_block_id, uow)
      if persisted.identity() == identity
    ]
    if len(matches) > 1:
      raise FeedGraphIntegrityError(
        f"feed {feed_block_id} has duplicate exact item identity {identity!r}"
      )
    return matches[0] if matches else None

  @classmethod
  async def _reconcile_enclosures(
    cls,
    item_block_id: int,
    canonical_enclosures: tuple[CanonicalEnclosure, ...],
    uow: GraphUnitOfWork,
  ) -> None:
    existing_relations = await uow.relations.get(
      item_block_id, include_in=False, content=ENCLOSURE_RELATION
    )
    blocks = {
      block.id: block
      for block in await uow.blocks.get_many(tuple(r.to_ for r in existing_relations))
    }
    by_url: dict[str, list[tuple[RelationModel, BlockModel]]] = {}
    for relation in existing_relations:
      block = blocks.get(relation.to_)
      if block is None or block.resolver != ENCLOSURE_RESOLVER_ID:
        raise FeedGraphIntegrityError(
          f"enclosure relation {relation.id} does not target exact metadata"
        )
      try:
        persisted = CanonicalEnclosure.model_validate_json(block.content)
      except ValueError as error:
        raise FeedGraphIntegrityError(
          f"enclosure block {block.id} has invalid canonical content"
        ) from error
      by_url.setdefault(persisted.url, []).append((relation, block))

    retained_relation_ids: set[int] = set()
    for canonical in canonical_enclosures:
      candidates = by_url.get(canonical.url, [])
      if candidates:
        relation, block = candidates.pop(0)
        await _replace_content(block, canonical.model_dump_json(), uow)
      else:
        block = await uow.blocks.create(
          BlockForm(
            resolver=ENCLOSURE_RESOLVER_ID,
            content=canonical.model_dump_json(),
          ),
        )
        relation = await uow.relations.create(
          item_block_id,
          _block_id(block),
          ENCLOSURE_RELATION,
        )
      if relation.id is not None:
        retained_relation_ids.add(relation.id)

    await uow.relations.delete_many(
      tuple(
        relation.id
        for relation in existing_relations
        if relation.id is not None and relation.id not in retained_relation_ids
      )
    )

  @classmethod
  async def reconcile_item(
    cls,
    feed_block_id: int,
    canonical: CanonicalFeedItem,
    enclosures: tuple[CanonicalEnclosure, ...],
  ) -> ReconcileResult:
    """Reconcile one item primary graph in its own serializable feed scope."""
    async with graph_uow() as uow:
      feed = await uow.blocks.get(feed_block_id, lock=True)
      if feed is None or feed.resolver != FEED_RESOLVER_ID:
        raise FeedGraphIntegrityError(f"feed {feed_block_id} does not exist")

      item = await cls._find_item(feed_block_id, canonical, uow)
      content = canonical.model_dump_json()
      if item is None:
        item = await uow.blocks.create(
          BlockForm(resolver=FEED_ITEM_RESOLVER_ID, content=content),
        )
        await uow.relations.create(
          _block_id(item),
          feed_block_id,
          FEED_RELATION,
        )
        action = "created"
        alternate_url_changed = True
      else:
        previous = CanonicalFeedItem.model_validate_json(item.content)
        changed = await _replace_content(item, content, uow)
        action = "updated" if changed else "unchanged"
        alternate_url_changed = previous.alternate_url != canonical.alternate_url

      await cls._reconcile_enclosures(_block_id(item), enclosures, uow)
      return ReconcileResult(_block_id(item), action, alternate_url_changed)


__all__ = [
  "CONTENT_RELATION",
  "ENCLOSURE_RELATION",
  "ENCLOSURE_RESOLVER_ID",
  "FEED_ITEM_RESOLVER_ID",
  "FEED_RELATION",
  "FEED_RESOLVER_ID",
  "FULL_TEXT_RELATION",
  "FeedGraphIntegrityError",
  "FeedGraphReconciler",
  "ReconcileResult",
]
