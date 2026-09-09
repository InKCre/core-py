"""Real PostgreSQL journey across exact Organization graph effects."""

import asyncio
import os
import uuid

import pytest
import sqlalchemy

from app.business.graph_navigation_retrieval import GraphNavigationRetrievalManager
from app.business.info_base import BlockManager
from app.business.info_base.resolver import register_core_resolvers
from app.business.organization import (
  DuplicateAssertionBehaviorResolver,
  EvidenceStanceBehaviorResolver,
  ExistingReferentAnchoringBehaviorResolver,
  RefinementBehaviorResolver,
  SupersessionBehaviorResolver,
  SynthesisBehaviorResolver,
  register_core_organization_behaviors,
)
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockForm


pytestmark = pytest.mark.skipif(
  not os.getenv("INKCRE_TEST_DATABASE_URL"),
  reason="requires an explicitly selected migrated PostgreSQL runtime",
)


def _cleanup(block_ids: list[int]) -> None:
  if not block_ids:
    return
  with SessionLocal() as db_session:
    db_session.connection().execute(
      sqlalchemy.text("DELETE FROM inkcre.blocks WHERE id = ANY(:ids)"),
      {"ids": block_ids},
    )
    db_session.commit()


def test_exact_behaviors_compose_into_replayable_graph_use() -> None:
  register_core_resolvers()
  register_core_organization_behaviors()
  marker = uuid.uuid4().hex
  persisted: list[int] = []

  try:
    with SessionLocal() as db_session:
      blocks = BlockManager.create_many(
        (
          BlockForm(resolver="core.text.v1", content=f"{marker}: old limit"),
          BlockForm(resolver="core.text.v1", content=f"{marker}: new limit"),
          BlockForm(resolver="core.text.v1", content=f"{marker}: detail"),
          BlockForm(resolver="core.text.v1", content=f"{marker}: measurement"),
          BlockForm(resolver="core.text.v1", content=f"{marker}: service record"),
          BlockForm(resolver="core.text.v1", content=f"{marker}: copied report"),
          BlockForm(resolver="core.text.v1", content=f"{marker}: relayed copy"),
        ),
        db_session,
      )
      ids = tuple(block.id for block in blocks if block.id is not None)
      assert len(ids) == 7
      persisted.extend(ids)
      old, new, detail, evidence, referent, copied, relayed = ids

      supersession = asyncio.run(
        SupersessionBehaviorResolver.record_supersession(
          new,
          old,
          db_session=db_session,
        )
      )
      refinement = asyncio.run(
        RefinementBehaviorResolver.record_refinement(
          detail,
          old,
          db_session=db_session,
        )
      )
      stance = asyncio.run(
        EvidenceStanceBehaviorResolver.record_evidence_stance(
          evidence,
          new,
          "supports",
          db_session=db_session,
        )
      )
      first_anchor = asyncio.run(
        ExistingReferentAnchoringBehaviorResolver.anchor_existing_referent(
          detail,
          "the service",
          referent,
          db_session=db_session,
        )
      )
      second_anchor = asyncio.run(
        ExistingReferentAnchoringBehaviorResolver.anchor_existing_referent(
          detail,
          "the service",
          referent,
          db_session=db_session,
        )
      )
      first_duplicate = asyncio.run(
        DuplicateAssertionBehaviorResolver.record_duplicate_assertion(
          copied,
          relayed,
          db_session=db_session,
        )
      )
      second_duplicate = asyncio.run(
        DuplicateAssertionBehaviorResolver.record_duplicate_assertion(
          relayed,
          old,
          db_session=db_session,
        )
      )
      synthesis = asyncio.run(
        SynthesisBehaviorResolver.create_synthesis(
          f"{marker}: reusable synthesis",
          (new, detail, evidence),
          db_session=db_session,
        )
      )
      replay = asyncio.run(
        SynthesisBehaviorResolver.create_synthesis(
          f"{marker}: reusable synthesis",
          (evidence, detail, new),
          db_session=db_session,
        )
      )
      changed = asyncio.run(
        SynthesisBehaviorResolver.create_synthesis(
          f"{marker}: changed synthesis",
          (new, detail, evidence),
          synthesis.synthesis,
          db_session=db_session,
        )
      )

      assert supersession.created
      assert refinement.created
      assert stance.created
      assert first_anchor.fragment_created
      assert second_anchor.fragment == first_anchor.fragment
      assert not second_anchor.fragment_created
      assert not second_anchor.refers_to.created
      assert first_duplicate.created and second_duplicate.created
      assert replay.synthesis == synthesis.synthesis
      assert not replay.synthesis_created
      assert changed.synthesis != synthesis.synthesis
      assert changed.edited is not None and changed.edited.created
      persisted.extend((first_anchor.fragment, synthesis.synthesis, changed.synthesis))

      with pytest.raises(ValueError, match="directed cycle"):
        asyncio.run(
          SupersessionBehaviorResolver.record_supersession(
            old,
            new,
            db_session=db_session,
          )
        )
      with pytest.raises(ValueError, match="opposite stance"):
        asyncio.run(
          EvidenceStanceBehaviorResolver.record_evidence_stance(
            evidence,
            new,
            "challenges",
            db_session=db_session,
          )
        )

      duplicate_components = GraphNavigationRetrievalManager.get_connected_components(
        (copied, old),
        contents=("duplicates assertion",),
        db_session=db_session,
      )
      assert duplicate_components.missing_seed_blocks == ()
      assert not duplicate_components.truncated
      assert duplicate_components.components[0].seed_blocks == (copied, old)
      assert set(duplicate_components.components[0].member_blocks) == {
        copied,
        relayed,
        old,
      }
      assert len(duplicate_components.proof_graph.relations) == 2
      db_session.commit()
  finally:
    _cleanup(persisted)


def test_connected_component_reports_missing_and_bounded_incomplete_proof() -> None:
  marker = uuid.uuid4().hex
  persisted: list[int] = []
  try:
    blocks = [
      BlockManager.create(BlockForm(resolver="core.text.v1", content=f"{marker}:{index}"))
      for index in range(3)
    ]
    ids = tuple(block.id for block in blocks if block.id is not None)
    assert len(ids) == 3
    persisted.extend(ids)
    left, bridge, right = ids
    from app.business.info_base import RelationManager

    RelationManager.create(left, bridge, "duplicates assertion")
    RelationManager.create(bridge, right, "duplicates assertion")

    result = GraphNavigationRetrievalManager.get_connected_components(
      (left, right, max(ids) + 1_000_000),
      contents=("duplicates assertion",),
      max_explored_blocks=3,
      max_explored_relations=1,
    )
    assert result.truncated
    assert result.missing_seed_blocks == (max(ids) + 1_000_000,)
    assert len(result.proof_graph.relations) <= 1
  finally:
    _cleanup(persisted)
