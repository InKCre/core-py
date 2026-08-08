"""Top-level memo-family state and keyset selection."""

import datetime

from app.schemas.info_base.block import BlockModel
from extensions.memos.family.graph import MEMO_RESOLVER, select_top_level_roots
from extensions.memos.family.schema import CanonicalMemo


def _block(block_id: int, hour: int, *, archived: bool = False) -> BlockModel:
  timestamp = datetime.datetime(2026, 8, 1, hour, tzinfo=datetime.UTC)
  canonical = CanonicalMemo(
    body=f"memo {block_id}",
    created_at=timestamp,
    updated_at=timestamp,
    archived=archived,
  )
  return BlockModel(
    id=block_id,
    resolver=MEMO_RESOLVER,
    content=canonical.to_block_content(),
  )


def test_top_level_query_excludes_comments_and_pages_by_canonical_time_and_id():
  roots = (
    _block(1, 7),
    _block(2, 8),
    _block(3, 8),
    _block(4, 9),
    _block(5, 10, archived=True),
  )

  first, cursor = select_top_level_roots(
    roots,
    parent_root_ids={4},
    archived=False,
    after=None,
    limit=2,
  )
  assert [block.id for block in first] == [3, 2]
  assert cursor is not None and cursor.block_id == 2

  # A concurrent newer insert does not shift or duplicate the second page.
  second, terminal = select_top_level_roots(
    (*roots, _block(6, 11)),
    parent_root_ids={4},
    archived=False,
    after=cursor,
    limit=2,
  )
  assert [block.id for block in second] == [1]
  assert terminal is None

  archived, terminal = select_top_level_roots(
    roots,
    parent_root_ids={4},
    archived=True,
    after=None,
    limit=2,
  )
  assert [block.id for block in archived] == [5]
  assert terminal is None


def test_large_top_level_batch_remains_bounded_to_requested_page():
  roots = tuple(_block(block_id, block_id % 24) for block_id in range(1, 2501))

  selected, cursor = select_top_level_roots(
    roots,
    parent_root_ids=set(),
    archived=False,
    after=None,
    limit=200,
  )

  assert len(selected) == 200
  assert cursor is not None
  assert len({block.id for block in selected}) == 200
