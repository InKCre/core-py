"""Real PostgreSQL proof for flat GraphForm submission semantics."""

import asyncio
import os
import uuid

import pytest
import sqlalchemy
import sqlmodel

from app.business.info_base.main import InfoBaseManager
from app.business.info_base.resolver import register_core_resolvers
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockForm, BlockModel
from app.schemas.info_base.main import (
  GraphBlockForm,
  GraphForm,
  GraphRelationForm,
  InArcForm,
  OutArcForm,
  StarsGraphForm,
)
from app.schemas.info_base.relation import RelationForm, RelationModel


pytestmark = pytest.mark.skipif(
  not os.getenv("INKCRE_TEST_DATABASE_URL"),
  reason="requires an explicitly selected migrated PostgreSQL runtime",
)


def _cleanup(block_ids: list[int]) -> None:
  if not block_ids:
    return
  with SessionLocal() as db:
    db.connection().execute(
      sqlalchemy.text("DELETE FROM inkcre.blocks WHERE id = ANY(:ids)"),
      {"ids": block_ids},
    )
    db.commit()


def test_submit_graph_creates_arbitrary_links_and_returns_only_block_mapping():
  persisted: list[int] = []
  graph = GraphForm(
    blocks=(
      GraphBlockForm(id=-4, resolver="core.text.v1", content="first"),
      GraphBlockForm(id=-5, resolver="core.text.v1", content="second"),
    ),
    relations=(
      GraphRelationForm(from_=-4, to_=-5, content="next"),
      GraphRelationForm(from_=-5, to_=-4, content="reference"),
    ),
  )

  try:
    result = InfoBaseManager.submit_graph(graph)
    persisted = [mapping.id for mapping in result.blocks]
    mapping = {item.local_id: item.id for item in result.blocks}

    assert result.model_dump() == {
      "blocks": (
        {"local_id": -4, "id": mapping[-4]},
        {"local_id": -5, "id": mapping[-5]},
      )
    }
    with SessionLocal() as db:
      blocks = tuple(db.get(BlockModel, block_id) for block_id in persisted)
      relations = db.exec(
        sqlmodel.select(RelationModel).where(RelationModel.from_.in_(persisted))  # pyrefly: ignore[missing-attribute]
      ).all()
    assert [block.content for block in blocks if block is not None] == [
      "first",
      "second",
    ]
    assert {(item.from_, item.content, item.to_) for item in relations} == {
      (mapping[-4], "next", mapping[-5]),
      (mapping[-5], "reference", mapping[-4]),
    }
  finally:
    _cleanup(persisted)


def test_repeating_negative_ids_requests_new_blocks_each_time():
  persisted: list[int] = []
  graph = GraphForm(
    blocks=(GraphBlockForm(id=-1, resolver="core.text.v1", content="repeat"),)
  )

  try:
    first = InfoBaseManager.submit_graph(graph).blocks[0].id
    second = InfoBaseManager.submit_graph(graph).blocks[0].id
    persisted.extend((first, second))

    assert first != second
  finally:
    _cleanup(persisted)


def test_recursive_stars_authoring_retains_reconciliation_and_direction():
  register_core_resolvers()
  marker = uuid.uuid4().hex
  contents = {
    "root": f"{marker}:root",
    "out": f"{marker}:out",
    "in": f"{marker}:in",
  }
  stars = StarsGraphForm(
    block=BlockForm(resolver="core.text.v1", content=contents["root"]),
    out_arcs=(
      OutArcForm(
        relation=RelationForm(content="outgoing"),
        to_graph=StarsGraphForm(
          block=BlockForm(resolver="core.text.v1", content=contents["out"])
        ),
      ),
    ),
    in_arcs=(
      InArcForm(
        relation=RelationForm(content="incoming"),
        from_graph=StarsGraphForm(
          block=BlockForm(resolver="core.text.v1", content=contents["in"])
        ),
      ),
    ),
  )

  try:
    with SessionLocal() as db:
      first_root = asyncio.run(InfoBaseManager.add_stars_graph_to_session(stars, db))
      db.commit()
      assert first_root.id is not None
      first_root_id = first_root.id

    with SessionLocal() as db:
      second_root = asyncio.run(InfoBaseManager.add_stars_graph_to_session(stars, db))
      db.commit()
      assert second_root.id == first_root_id

      blocks = db.exec(
        sqlmodel.select(BlockModel).where(BlockModel.content.in_(contents.values()))  # pyrefly: ignore[missing-attribute]
      ).all()
      block_ids = [block.id for block in blocks if block.id is not None]
      by_content = {block.content: block.id for block in blocks}
      relations = db.exec(
        sqlmodel.select(RelationModel).where(
          RelationModel.from_.in_(block_ids)  # pyrefly: ignore[missing-attribute]
        )
      ).all()

    assert len(blocks) == 3
    assert {(item.from_, item.content, item.to_) for item in relations} == {
      (by_content[contents["root"]], "outgoing", by_content[contents["out"]]),
      (by_content[contents["in"]], "incoming", by_content[contents["root"]]),
    }
  finally:
    with SessionLocal() as db:
      cleanup_ids = [
        block.id
        for block in db.exec(
          sqlmodel.select(BlockModel).where(
            BlockModel.content.in_(contents.values())  # pyrefly: ignore[missing-attribute]
          )
        ).all()
        if block.id is not None
      ]
    _cleanup(cleanup_ids)
