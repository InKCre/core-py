"""Provenance-preserving evidence stance relation behavior."""

from __future__ import annotations

import logging
import typing

import sqlmodel

from app.business.deployment_config import DeploymentConfigManager
from app.business.info_base.resolver import Resolver
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockID
from app.schemas.info_base.relation import RelationModel
from app.schemas.organization_behavior import (
  BehaviorAgentConfig,
  CandidateWriteResult,
  RelationWriteResult,
)

from ._shared import (
  build_seed_message,
  candidate_seed_ids,
  configured_agent_available,
  fetchsert_relation,
  merge_seed_categories,
  random_block_ids,
  recent_block_ids,
  recent_relation_endpoint_ids,
  record_candidate,
  relation_result,
  require_distinct_blocks,
  run_configured_agent,
)


LOGGER = logging.getLogger(__name__)

SUPPORTS_RELATION = "supports"
CHALLENGES_RELATION = "challenges"
EVIDENCE_STANCE_BEHAVIOR = "core.organization.behavior.evidence-stance.v1"
EVIDENCE_STANCE_CONFIG_KEY = "core.organization.evidence_stance"
EVIDENCE_STANCE_CONFIG_SCHEMA = "core.organization.evidence_stance.config.v1"

DeploymentConfigManager.register_schema(
  EVIDENCE_STANCE_CONFIG_SCHEMA,
  BehaviorAgentConfig,
)


class EvidenceStanceBehaviorResolver(
  Resolver[str, str],
  rso_type=EVIDENCE_STANCE_BEHAVIOR,
):
  organization_description = (
    "Relate attributable evidence that supports or challenges an assertion."
  )
  judgment_contract = (
    "Evidence and assertion are complete addressable information units.",
    "The source is evidence and the target is an evaluable assertion.",
    "Their proposition and applicable scope are comparable.",
    "The evidence genuinely changes reasons for the assertion.",
    "Evidence provenance and speaker attribution remain recoverable.",
    "The stance is unambiguously support or challenge for the whole assertion.",
    "Duplicate, refinement, replacement, or topical proximity alone is insufficient.",
  )

  async def get_text(
    self,
    *,
    context: typing.Literal["default", "lexical"] = "default",
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    del context, refresh, materialize_missing
    return self.organization_description

  async def get_label(self, *, refresh: bool = False) -> str:
    del refresh
    return "organization behavior: evidence stance"

  @classmethod
  async def record_candidate(
    cls,
    information_id: BlockID,
    *,
    db_session: sqlmodel.Session | None = None,
  ) -> CandidateWriteResult:
    return await record_candidate(cls, information_id, db_session=db_session)

  @classmethod
  async def record_evidence_stance(
    cls,
    evidence_id: BlockID,
    assertion_id: BlockID,
    stance: typing.Literal["supports", "challenges"],
    *,
    db_session: sqlmodel.Session | None = None,
  ) -> RelationWriteResult:
    if db_session is None:
      with SessionLocal() as owned_session:
        result = await cls.record_evidence_stance(
          evidence_id,
          assertion_id,
          stance,
          db_session=owned_session,
        )
        owned_session.commit()
        return result
    require_distinct_blocks(evidence_id, assertion_id, db_session)
    opposite = CHALLENGES_RELATION if stance == SUPPORTS_RELATION else SUPPORTS_RELATION
    existing_opposite = db_session.exec(
      sqlmodel.select(RelationModel.id).where(
        RelationModel.from_ == evidence_id,
        RelationModel.to_ == assertion_id,
        RelationModel.content == opposite,
      )
    ).first()
    if existing_opposite is not None:
      raise ValueError("The evidence/assertion pair already has the opposite stance")
    relation, created = fetchsert_relation(
      evidence_id,
      assertion_id,
      stance,
      db_session,
    )
    return relation_result(relation, created)

  @classmethod
  def can_run_automatic(cls) -> bool:
    return configured_agent_available(EVIDENCE_STANCE_CONFIG_KEY, BehaviorAgentConfig)

  @classmethod
  async def run_automatic(cls, max_seeds: int) -> None:
    candidates = await candidate_seed_ids(cls, max_seeds)
    strong = merge_seed_categories(
      max_seeds,
      recent_relation_endpoint_ids(max_seeds),
      recent_block_ids(max_seeds),
    )
    random = random_block_ids(max_seeds)
    seeds = merge_seed_categories(max_seeds, candidates, strong, random)
    LOGGER.info(
      "organization.seeds.selected",
      extra={
        "behavior": cls.__rsotype__,
        "max_seeds": max_seeds,
        "candidate_count": len(candidates),
        "strong_count": len(strong),
        "random_count": len(random),
        "seed_block_ids": seeds,
      },
    )
    for seed in seeds:
      message = await build_seed_message(
        "Determine only attributable evidence support or challenge relations.",
        cls.judgment_contract,
        seed,
      )
      if message is None:
        LOGGER.info(
          "organization.seed.considered",
          extra={
            "behavior": cls.__rsotype__,
            "seed_block_ids": (seed,),
            "outcome": "unresolved",
            "reason": "text_unavailable",
          },
        )
        continue
      await run_configured_agent(
        EVIDENCE_STANCE_CONFIG_KEY,
        BehaviorAgentConfig,
        message,
      )
      LOGGER.info(
        "organization.seed.considered",
        extra={
          "behavior": cls.__rsotype__,
          "seed_block_ids": (seed,),
          "outcome": "considered",
          "reason": "agent_completed",
        },
      )
