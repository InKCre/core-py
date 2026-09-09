"""Small shared mechanics for exact Organization behaviors."""

from __future__ import annotations

import json
import typing

import pydantic
import sqlalchemy
import sqlmodel

from app.business.agent import AgentManager, AgentNotFoundError, TurnTermination
from app.business.deployment_config import DeploymentConfigManager
from app.business.info_base.block import BlockManager
from app.business.info_base.relation import RelationManager
from app.business.info_base.resolver import (
  Resolver,
  ResolverManager,
  UnknownResolverError,
  UnsupportedResolverCapability,
)
from app.engine import SessionLocal
from app.schemas.ai import TextContentPart, UserMessage
from app.schemas.info_base.block import BlockForm, BlockID, BlockModel, ResolverType
from app.schemas.info_base.relation import RelationID, RelationModel
from app.schemas.organization_behavior import CandidateWriteResult, RelationWriteResult

from .contracts import (
  OrganizationAgentNotFoundError,
  OrganizationBlockNotFoundError,
  OrganizationExecutionError,
  OrganizationNotConfiguredError,
)


CANDIDATE_RELATION = "candidate for"
_CONTEXT_RELATION_LIMIT = 20


def behavior_resolver_classes() -> tuple[type[Resolver], ...]:
  classes: list[type[Resolver]] = []
  for resolver_cls in ResolverManager.RESOLVER_CLS.values():
    if (
      issubclass(resolver_cls, Resolver)
      and isinstance(getattr(resolver_cls, "organization_description", None), str)
      and callable(getattr(resolver_cls, "record_candidate", None))
      and callable(getattr(resolver_cls, "can_run_automatic", None))
      and callable(getattr(resolver_cls, "run_automatic", None))
    ):
      classes.append(resolver_cls)
  return tuple(sorted(classes, key=lambda resolver_cls: resolver_cls.__rsotype__))


def get_behavior_resolver(resolver: ResolverType) -> type[Resolver] | None:
  return next(
    (
      resolver_cls
      for resolver_cls in behavior_resolver_classes()
      if resolver_cls.__rsotype__ == resolver
    ),
    None,
  )


async def get_or_create_descriptor(
  behavior: type[Resolver],
  db_session: sqlmodel.Session,
) -> BlockModel:
  return await BlockManager.fetchsert(
    BlockForm(resolver=behavior.__rsotype__, content=""),
    db_session,
  )


async def record_candidate(
  behavior: type[Resolver],
  information_id: BlockID,
  *,
  db_session: sqlmodel.Session | None = None,
) -> CandidateWriteResult:
  if db_session is None:
    with SessionLocal() as owned_session:
      result = await record_candidate(
        behavior,
        information_id,
        db_session=owned_session,
      )
      owned_session.commit()
      return result
  if BlockManager.get(information_id, db_session) is None:
    raise OrganizationBlockNotFoundError(f"Block {information_id} does not exist")
  descriptor = await get_or_create_descriptor(behavior, db_session)
  descriptor_id = _block_id(descriptor)
  if information_id == descriptor_id:
    raise ValueError("An Organization behavior cannot be its own candidate")
  relation, created = fetchsert_relation(
    information_id,
    descriptor_id,
    CANDIDATE_RELATION,
    db_session,
  )
  return CandidateWriteResult(
    descriptor=descriptor_id,
    relation=_relation_id(relation),
    created=created,
  )


async def candidate_seed_ids(
  behavior: type[Resolver],
  limit: int,
) -> tuple[BlockID, ...]:
  if limit <= 0:
    return ()
  with SessionLocal() as db_session:
    descriptor = await get_or_create_descriptor(behavior, db_session)
    descriptor_id = _block_id(descriptor)
    statement = (
      sqlmodel.select(RelationModel.from_)
      .where(
        RelationModel.to_ == descriptor_id,
        RelationModel.content == CANDIDATE_RELATION,
      )
      .order_by(sqlalchemy.func.random())
      .limit(limit)
    )
    seeds = tuple(db_session.exec(statement).all())
    db_session.commit()
    return seeds


def recent_block_ids(limit: int) -> tuple[BlockID, ...]:
  if limit <= 0:
    return ()
  behavior_types = tuple(
    resolver_cls.__rsotype__ for resolver_cls in behavior_resolver_classes()
  )
  statement = sqlmodel.select(BlockModel.id).where(BlockModel.id.is_not(None))  # type: ignore[union-attr]
  if behavior_types:
    statement = statement.where(BlockModel.resolver.not_in(behavior_types))  # type: ignore[union-attr]
  statement = statement.order_by(
    sqlmodel.desc(BlockModel.updated_at),
    sqlmodel.desc(BlockModel.id),
  ).limit(limit)
  with SessionLocal() as db_session:
    return tuple(typing.cast(BlockID, value) for value in db_session.exec(statement).all())


def random_block_ids(limit: int) -> tuple[BlockID, ...]:
  if limit <= 0:
    return ()
  behavior_types = tuple(
    resolver_cls.__rsotype__ for resolver_cls in behavior_resolver_classes()
  )
  statement = sqlmodel.select(BlockModel.id).where(BlockModel.id.is_not(None))  # type: ignore[union-attr]
  if behavior_types:
    statement = statement.where(BlockModel.resolver.not_in(behavior_types))  # type: ignore[union-attr]
  statement = statement.order_by(sqlalchemy.func.random()).limit(limit)
  with SessionLocal() as db_session:
    return tuple(typing.cast(BlockID, value) for value in db_session.exec(statement).all())


def recent_relation_endpoint_ids(
  limit: int,
  *,
  contents: typing.Collection[str] = (),
) -> tuple[BlockID, ...]:
  if limit <= 0:
    return ()
  statement = sqlmodel.select(RelationModel).order_by(
    sqlmodel.desc(RelationModel.updated_at),
    sqlmodel.desc(RelationModel.id),
  )
  if contents:
    statement = statement.where(RelationModel.content.in_(tuple(contents)))  # type: ignore[union-attr]
  statement = statement.limit(limit)
  with SessionLocal() as db_session:
    relations = db_session.exec(statement).all()
  return tuple(
    dict.fromkeys(
      endpoint for relation in relations for endpoint in (relation.from_, relation.to_)
    )
  )


def merge_seed_categories(
  max_seeds: int,
  *categories: typing.Collection[BlockID],
) -> tuple[BlockID, ...]:
  """Reserve one position per non-empty category, then fill in priority order."""
  result: list[BlockID] = []
  normalized = [tuple(dict.fromkeys(category)) for category in categories]
  for category in normalized:
    if category and category[0] not in result:
      result.append(category[0])
      if len(result) == max_seeds:
        return tuple(result)
  for category in normalized:
    for block_id in category[1:]:
      if block_id not in result:
        result.append(block_id)
        if len(result) == max_seeds:
          return tuple(result)
  return tuple(result)


def configured_agent_available(
  config_key: str,
  config_type: type[pydantic.BaseModel],
) -> bool:
  config = DeploymentConfigManager.get(config_key)
  if config is None:
    return False
  if not isinstance(config, config_type):
    raise TypeError(f"Organization config {config_key!r} returned the wrong model")
  return AgentManager.can_execute(typing.cast(typing.Any, config).agent, "text")


async def run_configured_agent(
  config_key: str,
  config_type: type[pydantic.BaseModel],
  message: UserMessage,
) -> None:
  config = DeploymentConfigManager.get(config_key)
  if config is None:
    raise OrganizationNotConfiguredError(
      f"Organization behavior {config_key!r} is not configured"
    )
  if not isinstance(config, config_type):
    raise TypeError(f"Organization config {config_key!r} returned the wrong model")
  agent_id = typing.cast(typing.Any, config).agent
  try:
    thread = await AgentManager.run(agent_id, message)
  except AgentNotFoundError as error:
    raise OrganizationAgentNotFoundError(
      f"Configured Organization Agent {agent_id} does not exist"
    ) from error
  turn = thread.current_turn
  if turn is None:  # pragma: no cover - AgentManager.run invariant
    raise OrganizationExecutionError("Organization Agent did not start a Turn")
  outcome = await turn
  if outcome == TurnTermination.MAX_MODEL_CALLS:
    raise OrganizationExecutionError(
      "Organization Agent exceeded its per-Turn model-call budget"
    )


async def build_seed_message(
  request: str,
  judgment_contract: tuple[str, ...],
  seed_id: BlockID,
) -> UserMessage | None:
  """Resolve one bounded seed neighborhood without holding a DB transaction."""
  with SessionLocal() as db_session:
    block = BlockManager.get(seed_id, db_session)
    if block is None:
      raise OrganizationBlockNotFoundError(f"Block {seed_id} does not exist")
    relations = tuple(
      sorted(
        RelationManager.get(seed_id, db_session=db_session),
        key=lambda relation: relation.id or 0,
      )[-_CONTEXT_RELATION_LIMIT:]
    )
    neighbor_ids = {
      relation.to_ if relation.from_ == seed_id else relation.from_
      for relation in relations
    }
    neighbors = {
      neighbor.id: neighbor
      for neighbor in BlockManager.get_many(neighbor_ids, db_session)
      if neighbor.id is not None
    }

  try:
    resolver = ResolverManager.get(block)
    text = await resolver.get_text(materialize_missing=False)
    label = await resolver.get_label()
  except (UnknownResolverError, UnsupportedResolverCapability):
    return None
  if text is None or not text.strip():
    return None

  relation_context: list[dict[str, typing.Any]] = []
  for relation in relations:
    other_id = relation.to_ if relation.from_ == seed_id else relation.from_
    other = neighbors.get(other_id)
    other_label = None
    if other is not None:
      try:
        other_label = await ResolverManager.get(other).get_label()
      except (UnknownResolverError, UnsupportedResolverCapability):
        pass
    relation_context.append(
      {
        "id": relation.id,
        "direction": "outgoing" if relation.from_ == seed_id else "incoming",
        "content": relation.content,
        "other_block": {
          "id": other_id,
          "resolver": other.resolver if other is not None else None,
          "label": other_label,
        },
      }
    )
  context = {
    "request": request,
    "judgment_contract": judgment_contract,
    "seed_block": {
      "id": seed_id,
      "resolver": block.resolver,
      "label": label,
      "text": text,
    },
    "direct_relations": relation_context,
    "exploration": (
      "The seed and its direct relations are only a starting point. Use the declared "
      "retrieval, Resolver, and graph tools when more evidence is needed. Persist only "
      "through the exact behavior tool, or cautiously mark a different behavior candidate."
    ),
  }
  return UserMessage(
    content=(
      TextContentPart(
        text=json.dumps(
          context,
          ensure_ascii=False,
          sort_keys=True,
          separators=(",", ":"),
        )
      ),
    )
  )


def fetchsert_relation(
  from_: BlockID,
  to_: BlockID,
  content: str,
  db_session: sqlmodel.Session,
) -> tuple[RelationModel, bool]:
  proposed = RelationModel(from_=from_, to_=to_, content=content)
  relation = RelationManager.fetchsert(proposed, db_session)
  return relation, relation is proposed


def relation_result(relation: RelationModel, created: bool) -> RelationWriteResult:
  return RelationWriteResult(relation=_relation_id(relation), created=created)


def require_distinct_blocks(
  left: BlockID,
  right: BlockID,
  db_session: sqlmodel.Session,
) -> None:
  if left == right:
    raise ValueError("Organization relation endpoints must be different")
  found = {block.id for block in BlockManager.get_many((left, right), db_session)}
  missing = tuple(block_id for block_id in (left, right) if block_id not in found)
  if missing:
    raise OrganizationBlockNotFoundError(f"Blocks do not exist: {missing!r}")


def _block_id(block: BlockModel) -> BlockID:
  if block.id is None:  # pragma: no cover - persisted Block invariant
    raise RuntimeError("Persisted Block has no ID")
  return block.id


def _relation_id(relation: RelationModel) -> RelationID:
  if relation.id is None:  # pragma: no cover - persisted Relation invariant
    raise RuntimeError("Persisted Relation has no ID")
  return relation.id
