"""Comment ownership traversal and no-over-delete contracts."""

from app.business.info_base.block import BlockManager
from app.business.info_base.relation import RelationManager
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel
from extensions.memos.family.graph import (
  ATTACHMENT_RESOLVER,
  MEMO_RESOLVER,
  MemoGraphRepository,
)


def test_owned_delete_plan_is_postorder_bounded_and_ignores_references(monkeypatch):
  relations = (
    RelationModel(id=1, from_=2, to_=1, content="parent"),
    RelationModel(id=2, from_=3, to_=2, content="parent"),
    RelationModel(id=3, from_=4, to_=1, content="parent"),
    RelationModel(id=4, from_=4, to_=99, content="parent"),
    RelationModel(id=5, from_=1, to_=10, content="attachment:0"),
    RelationModel(id=6, from_=2, to_=11, content="attachment:0"),
    RelationModel(id=7, from_=1, to_=12, content="attachment:1"),
    RelationModel(id=8, from_=99, to_=12, content="attachment:0"),
    RelationModel(id=9, from_=1, to_=77, content="reference"),
  )
  memo_ids = {1, 2, 3, 4, 77, 99}
  attachments = {
    block_id: BlockModel(
      id=block_id,
      resolver=ATTACHMENT_RESOLVER,
      content="{}",
    )
    for block_id in (10, 11, 12)
  }

  def get_relations(
    _cls,
    block_id,
    include_in=True,
    include_out=True,
    content=None,
    db_session=None,
  ):
    del db_session
    selected = tuple(
      relation
      for relation in relations
      if (
        (include_in and relation.to_ == block_id)
        or (include_out and relation.from_ == block_id)
      )
      and (content is None or relation.content == content)
    )
    return selected

  monkeypatch.setattr(RelationManager, "get", classmethod(get_relations))
  monkeypatch.setattr(
    BlockManager,
    "get",
    classmethod(lambda _cls, block_id, _session=None: attachments.get(block_id)),
  )
  monkeypatch.setattr(
    MemoGraphRepository,
    "get_root",
    classmethod(
      lambda _cls, block_id, _session: (
        BlockModel(id=block_id, resolver=MEMO_RESOLVER, content="{}")
        if block_id in memo_ids
        else None
      )
    ),
  )

  plan = MemoGraphRepository.owned_deletion_plan(1, object())  # type: ignore[arg-type]

  assert plan.comment_ids == (3, 2)
  assert plan.attachment_ids == (10, 11)
  assert 4 not in plan.comment_ids
  assert 12 not in plan.attachment_ids
  assert 77 not in plan.comment_ids


def test_owned_delete_plan_stops_on_a_corrupt_parent_cycle(monkeypatch):
  relations = (
    RelationModel(id=1, from_=2, to_=1, content="parent"),
    RelationModel(id=2, from_=1, to_=2, content="parent"),
  )

  def get_relations(
    _cls,
    block_id,
    include_in=True,
    include_out=True,
    content=None,
    db_session=None,
  ):
    del db_session
    return tuple(
      relation
      for relation in relations
      if (
        (include_in and relation.to_ == block_id)
        or (include_out and relation.from_ == block_id)
      )
      and (content is None or relation.content == content)
    )

  monkeypatch.setattr(RelationManager, "get", classmethod(get_relations))
  monkeypatch.setattr(
    MemoGraphRepository,
    "get_root",
    classmethod(
      lambda _cls, block_id, _session: (
        BlockModel(
          id=block_id,
          resolver=MEMO_RESOLVER,
          content="{}",
        )
        if block_id in {1, 2}
        else None
      )
    ),
  )

  plan = MemoGraphRepository.owned_deletion_plan(1, object())  # type: ignore[arg-type]

  assert plan.comment_ids == (2,)
  assert plan.attachment_ids == ()


def test_owned_delete_plan_uses_an_explicit_stack_for_deep_comment_trees(
  monkeypatch,
):
  depth = 1500
  incoming: dict[int, list[RelationModel]] = {}
  outgoing: dict[int, list[RelationModel]] = {}
  for child_id in range(2, depth + 1):
    relation = RelationModel(
      id=child_id,
      from_=child_id,
      to_=child_id - 1,
      content="parent",
    )
    incoming.setdefault(child_id - 1, []).append(relation)
    outgoing.setdefault(child_id, []).append(relation)

  def get_relations(
    _cls,
    block_id,
    include_in=True,
    include_out=True,
    content=None,
    db_session=None,
  ):
    del db_session
    values = []
    if include_in:
      values.extend(incoming.get(block_id, ()))
    if include_out:
      values.extend(outgoing.get(block_id, ()))
    return tuple(
      relation for relation in values if content is None or relation.content == content
    )

  monkeypatch.setattr(RelationManager, "get", classmethod(get_relations))
  monkeypatch.setattr(
    MemoGraphRepository,
    "get_root",
    classmethod(
      lambda _cls, block_id, _session: (
        BlockModel(
          id=block_id,
          resolver=MEMO_RESOLVER,
          content="{}",
        )
        if 1 <= block_id <= depth
        else None
      )
    ),
  )

  plan = MemoGraphRepository.owned_deletion_plan(1, object())  # type: ignore[arg-type]

  assert len(plan.comment_ids) == depth - 1
  assert plan.comment_ids[0] == depth
  assert plan.comment_ids[-1] == 2
