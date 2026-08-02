"""Memo-family graph grammar and persistence mapping."""

import datetime
from dataclasses import dataclass

import sqlmodel

from app.business.info_base.block import BlockManager
from app.business.info_base.relation import RelationManager
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel
from .schema import CanonicalMemo, MemoCursor


MEMO_RESOLVER = "extensions.memos.memo.v1"
ATTACHMENT_RESOLVER = "extensions.memos.attachment.v2"
ATTACHMENT_RELATION_PREFIX = "attachment:"
CONTENT_RELATION = "content"
PARENT_RELATION = "parent"
REFERENCE_RELATION = "reference"


@dataclass(frozen=True)
class MemoLinks:
  attachment_ids: tuple[int, ...]
  parent_id: int | None
  reference_ids: tuple[int, ...]


@dataclass(frozen=True)
class OwnedDeletionPlan:
  """Exclusively-owned descendants eligible for best-effort cleanup."""

  comment_ids: tuple[int, ...]
  attachment_ids: tuple[int, ...]


def solve_memo_links(block_id: int, relations: tuple[RelationModel, ...]) -> MemoLinks:
  """Interpret only outgoing relations that are properties of this memo root."""
  attachments: dict[int, int] = {}
  parent_id: int | None = None
  references: list[int] = []

  for relation in relations:
    if relation.from_ != block_id:
      continue
    if relation.content.startswith(ATTACHMENT_RELATION_PREFIX):
      raw_position = relation.content.removeprefix(ATTACHMENT_RELATION_PREFIX)
      if not raw_position.isdigit():
        raise ValueError(f"Invalid attachment relation: {relation.content}")
      position = int(raw_position)
      if position in attachments:
        raise ValueError(f"Duplicate attachment position: {position}")
      attachments[position] = relation.to_
    elif relation.content == PARENT_RELATION:
      if parent_id is not None:
        raise ValueError("Memo has more than one parent relation")
      parent_id = relation.to_
    elif relation.content == REFERENCE_RELATION:
      references.append(relation.to_)

  if attachments and sorted(attachments) != list(range(len(attachments))):
    raise ValueError("Attachment positions must be contiguous and zero-based")

  return MemoLinks(
    attachment_ids=tuple(attachments[index] for index in sorted(attachments)),
    parent_id=parent_id,
    reference_ids=tuple(references),
  )


class MemoGraphRepository:
  """Persist memo-family roots without product DTO or transport knowledge."""

  @classmethod
  def create_root(
    cls,
    canonical: CanonicalMemo,
    db_session: sqlmodel.Session,
  ) -> BlockModel:
    return BlockManager.create(
      BlockModel(
        resolver=MEMO_RESOLVER,
        content=canonical.to_block_content(),
      ),
      db_session,
    )

  @classmethod
  def get_root(
    cls,
    block_id: int,
    db_session: sqlmodel.Session,
  ) -> BlockModel | None:
    block = BlockManager.get(block_id, db_session)
    if block is None or block.resolver != MEMO_RESOLVER:
      return None
    return block

  @classmethod
  def create_comment(
    cls,
    parent_id: int,
    canonical: CanonicalMemo,
    db_session: sqlmodel.Session,
  ) -> BlockModel:
    if cls.get_root(parent_id, db_session) is None:
      raise LookupError(f"Memo memos/{parent_id} not found")
    block = cls.create_root(canonical, db_session)
    if block.id is None:
      raise RuntimeError("Persisted memo comment has no ID")
    RelationManager.create(
      block.id,
      parent_id,
      PARENT_RELATION,
      db_session,
    )
    return block

  @classmethod
  def list_comment_roots(
    cls,
    parent_id: int,
    *,
    limit: int,
    after_block_id: int | None,
    db_session: sqlmodel.Session,
  ) -> tuple[tuple[BlockModel, ...], int | None, int]:
    if limit <= 0:
      raise ValueError("comment page limit must be positive")
    if cls.get_root(parent_id, db_session) is None:
      raise LookupError(f"Memo memos/{parent_id} not found")

    child_ids = {
      relation.from_
      for relation in RelationManager.get(
        parent_id,
        include_in=True,
        include_out=False,
        content=PARENT_RELATION,
        db_session=db_session,
      )
      if relation.to_ == parent_id
    }
    roots = tuple(
      block
      for child_id in child_ids
      if (block := cls.get_root(child_id, db_session)) is not None and block.id is not None
    )
    ordered = sorted(roots, key=lambda block: block.id or 0, reverse=True)
    if after_block_id is not None:
      ordered = [block for block in ordered if (block.id or 0) < after_block_id]
    selected = ordered[:limit]
    next_block_id = None
    if len(ordered) > limit and selected:
      next_block_id = selected[-1].id
    return tuple(selected), next_block_id, len(roots)

  @classmethod
  def owned_deletion_plan(
    cls,
    root_id: int,
    db_session: sqlmodel.Session,
  ) -> OwnedDeletionPlan:
    """Traverse only exclusive parent/attachment ownership, never references."""
    if cls.get_root(root_id, db_session) is None:
      raise LookupError(f"Memo memos/{root_id} not found")

    visited: set[int] = set()
    comment_ids: list[int] = []
    attachment_ids: list[int] = []

    stack: list[tuple[int, bool]] = [(root_id, False)]
    while stack:
      memo_id, expanded = stack.pop()
      if expanded:
        if memo_id != root_id:
          comment_ids.append(memo_id)
        continue
      if memo_id in visited:
        continue
      visited.add(memo_id)
      relations = RelationManager.get(
        memo_id,
        include_in=True,
        include_out=True,
        db_session=db_session,
      )

      for relation in relations:
        if relation.from_ != memo_id or not relation.content.startswith(
          ATTACHMENT_RELATION_PREFIX
        ):
          continue
        component = BlockManager.get(relation.to_, db_session)
        if component is None or component.resolver != ATTACHMENT_RESOLVER:
          continue
        owners = tuple(
          candidate
          for candidate in RelationManager.get(
            relation.to_,
            include_in=True,
            include_out=False,
            db_session=db_session,
          )
          if candidate.content.startswith(ATTACHMENT_RELATION_PREFIX)
        )
        if len(owners) == 1 and owners[0].from_ == memo_id:
          attachment_ids.append(relation.to_)

      stack.append((memo_id, True))
      for relation in relations:
        if relation.to_ != memo_id or relation.content != PARENT_RELATION:
          continue
        child_id = relation.from_
        parents = RelationManager.get(
          child_id,
          include_in=False,
          include_out=True,
          content=PARENT_RELATION,
          db_session=db_session,
        )
        if (
          len(parents) != 1
          or parents[0].to_ != memo_id
          or cls.get_root(child_id, db_session) is None
        ):
          continue
        if child_id not in visited:
          stack.append((child_id, False))

    return OwnedDeletionPlan(
      comment_ids=tuple(comment_ids),
      attachment_ids=tuple(dict.fromkeys(attachment_ids)),
    )


def select_top_level_roots(
  blocks: tuple[BlockModel, ...],
  *,
  parent_root_ids: set[int],
  archived: bool,
  after: MemoCursor | None,
  limit: int,
) -> tuple[tuple[BlockModel, ...], MemoCursor | None]:
  """Apply family state/top-level/keyset semantics to resolver roots."""
  if limit <= 0:
    raise ValueError("memo page limit must be positive")

  dated: list[tuple[datetime.datetime, int, BlockModel]] = []
  for block in blocks:
    if block.id is None or block.id in parent_root_ids:
      continue
    canonical = CanonicalMemo.from_block_content(block.content)
    if canonical.archived != archived:
      continue
    sort_time = canonical.created_at or datetime.datetime.min.replace(tzinfo=datetime.UTC)
    dated.append((sort_time, block.id, block))

  dated.sort(key=lambda item: (item[0], item[1]), reverse=True)
  if after is not None:
    after_time = after.created_at or datetime.datetime.min.replace(tzinfo=datetime.UTC)
    dated = [item for item in dated if (item[0], item[1]) < (after_time, after.block_id)]

  selected = dated[:limit]
  next_cursor = None
  if len(dated) > limit and selected:
    last = selected[-1]
    last_canonical = CanonicalMemo.from_block_content(last[2].content)
    next_cursor = MemoCursor(created_at=last_canonical.created_at, block_id=last[1])
  return tuple(item[2] for item in selected), next_cursor
