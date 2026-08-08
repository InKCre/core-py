"""Session-aware graph primitives required by application-owned commands."""

import asyncio

import sqlalchemy.dialects.postgresql

from app.business.info_base.relation import RelationManager
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel
from extensions.memos.family.resolver import MemoResolver
from extensions.memos.family.schema import CanonicalMemo


class _Result:
  def all(self):
    return []


class _CaptureSession:
  statement = None

  def exec(self, statement):
    self.statement = statement
    return _Result()


def test_relation_query_uses_union_when_both_directions_are_requested():
  session = _CaptureSession()

  RelationManager.get(7, db_session=session)  # type: ignore[arg-type]

  assert session.statement is not None
  compiled = str(
    session.statement.compile(
      dialect=sqlalchemy.dialects.postgresql.dialect(),
      compile_kwargs={"literal_binds": True},
    )
  )
  assert "relations.to_ = 7 OR inkcre.relations.from_ = 7" in compiled


def test_resolver_relation_cache_is_scoped_by_requested_direction(monkeypatch):
  calls: list[tuple[bool, bool]] = []

  def get_relations(_cls, block_id, include_in=True, include_out=True, **_kwargs):
    assert block_id == 7
    calls.append((include_in, include_out))
    return ()

  monkeypatch.setattr(RelationManager, "get", classmethod(get_relations))
  canonical = CanonicalMemo(
    body="cache proof",
    created_at=None,
    updated_at=None,
  )
  resolver = MemoResolver(
    BlockModel(
      id=7,
      resolver=MemoResolver.__rsotype__,
      content=canonical.to_block_content(),
    )
  )

  asyncio.run(resolver.get_relations(include_in=False, include_out=True))
  asyncio.run(resolver.get_relations(include_in=True, include_out=False))
  asyncio.run(resolver.get_relations(include_in=False, include_out=True))

  assert calls == [(False, True), (True, False)]


def test_provided_full_relation_set_is_filtered_without_database_access(monkeypatch):
  monkeypatch.setattr(
    RelationManager,
    "get",
    classmethod(lambda cls, *args, **kwargs: (_ for _ in ()).throw(AssertionError())),
  )
  canonical = CanonicalMemo(body="provided", created_at=None, updated_at=None)
  resolver = MemoResolver(
    BlockModel(
      id=7,
      resolver=MemoResolver.__rsotype__,
      content=canonical.to_block_content(),
    ),
    (
      RelationModel(from_=7, to_=8, content="reference"),
      RelationModel(from_=9, to_=7, content="reference"),
    ),
  )

  outgoing = asyncio.run(resolver.get_relations(include_in=False, include_out=True))
  incoming = asyncio.run(resolver.get_relations(include_in=True, include_out=False))

  assert [(item.from_, item.to_) for item in outgoing] == [(7, 8)]
  assert [(item.from_, item.to_) for item in incoming] == [(9, 7)]
