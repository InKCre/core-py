"""Transactional reconciliation of canonical feed graphs."""

from __future__ import annotations

import dataclasses

import sqlmodel

from app.business.info_base.block import BlockManager
from app.business.info_base.relation import RelationManager
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockForm, BlockModel
from app.schemas.info_base.relation import RelationModel
from app.schemas.source import SourceModel

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


def _replace_content(
  block: BlockModel,
  content: str,
  db_session: sqlmodel.Session,
) -> bool:
  if block.content == content:
    return False
  block.content = content
  db_session.add(block)
  db_session.flush()
  db_session.refresh(block)
  return True


class FeedGraphRepository:
  """Own graph reconciliation mechanics without owning source policy."""

  @classmethod
  def reconcile_feed(cls, canonical: CanonicalFeed) -> ReconcileResult:
    with SessionLocal() as db_session:
      db_session.exec(
        sqlmodel.select(SourceModel)
        .where(SourceModel.id == canonical.source_instance_id)
        .with_for_update()
      ).one()
      matches: list[BlockModel] = []
      for block in db_session.exec(
        sqlmodel.select(BlockModel).where(BlockModel.resolver == FEED_RESOLVER_ID)
      ).all():
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
        changed = _replace_content(feed, content, db_session)
        result = ReconcileResult(_block_id(feed), "updated" if changed else "unchanged")
      else:
        feed = BlockManager.create(
          BlockForm(resolver=FEED_RESOLVER_ID, content=content),
          db_session,
        )
        result = ReconcileResult(_block_id(feed), "created")
      db_session.commit()
      return result

  @classmethod
  def _item_roots(
    cls,
    feed_block_id: int,
    db_session: sqlmodel.Session,
  ) -> tuple[tuple[BlockModel, CanonicalFeedItem], ...]:
    relations = db_session.exec(
      sqlmodel.select(RelationModel).where(
        RelationModel.to_ == feed_block_id,
        RelationModel.content == FEED_RELATION,
      )
    ).all()
    roots: list[tuple[BlockModel, CanonicalFeedItem]] = []
    for relation in relations:
      block = db_session.get(BlockModel, relation.from_)
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
  def _find_item(
    cls,
    feed_block_id: int,
    canonical: CanonicalFeedItem,
    db_session: sqlmodel.Session,
  ) -> BlockModel | None:
    identity = canonical.identity()
    if identity is None:
      return None
    matches = [
      block
      for block, persisted in cls._item_roots(feed_block_id, db_session)
      if persisted.identity() == identity
    ]
    if len(matches) > 1:
      raise FeedGraphIntegrityError(
        f"feed {feed_block_id} has duplicate exact item identity {identity!r}"
      )
    return matches[0] if matches else None

  @classmethod
  def _reconcile_enclosures(
    cls,
    item_block_id: int,
    canonical_enclosures: tuple[CanonicalEnclosure, ...],
    db_session: sqlmodel.Session,
  ) -> None:
    existing_relations = db_session.exec(
      sqlmodel.select(RelationModel).where(
        RelationModel.from_ == item_block_id,
        RelationModel.content == ENCLOSURE_RELATION,
      )
    ).all()
    by_url: dict[str, list[tuple[RelationModel, BlockModel]]] = {}
    for relation in existing_relations:
      block = db_session.get(BlockModel, relation.to_)
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
        _replace_content(block, canonical.model_dump_json(), db_session)
      else:
        block = BlockManager.create(
          BlockForm(
            resolver=ENCLOSURE_RESOLVER_ID,
            content=canonical.model_dump_json(),
          ),
          db_session,
        )
        relation = RelationManager.create(
          item_block_id,
          _block_id(block),
          ENCLOSURE_RELATION,
          db_session,
        )
      if relation.id is not None:
        retained_relation_ids.add(relation.id)

    for relation in existing_relations:
      if relation.id not in retained_relation_ids:
        db_session.delete(relation)
    db_session.flush()

  @classmethod
  def reconcile_item(
    cls,
    feed_block_id: int,
    canonical: CanonicalFeedItem,
    enclosures: tuple[CanonicalEnclosure, ...],
  ) -> ReconcileResult:
    """Reconcile one item primary graph in its own serializable feed scope."""
    with SessionLocal() as db_session:
      feed = db_session.exec(
        sqlmodel.select(BlockModel)
        .where(
          BlockModel.id == feed_block_id,
          BlockModel.resolver == FEED_RESOLVER_ID,
        )
        .with_for_update()
      ).one()
      del feed

      item = cls._find_item(feed_block_id, canonical, db_session)
      content = canonical.model_dump_json()
      if item is None:
        item = BlockManager.create(
          BlockForm(resolver=FEED_ITEM_RESOLVER_ID, content=content),
          db_session,
        )
        RelationManager.create(
          _block_id(item),
          feed_block_id,
          FEED_RELATION,
          db_session,
        )
        action = "created"
        alternate_url_changed = True
      else:
        previous = CanonicalFeedItem.model_validate_json(item.content)
        changed = _replace_content(item, content, db_session)
        action = "updated" if changed else "unchanged"
        alternate_url_changed = previous.alternate_url != canonical.alternate_url

      cls._reconcile_enclosures(_block_id(item), enclosures, db_session)
      db_session.commit()
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
  "FeedGraphRepository",
  "ReconcileResult",
]
