"""Profile-scoped embedding maintenance and exact semantic retrieval."""

from __future__ import annotations

from dataclasses import dataclass
import datetime
import logging
import math
import typing

import pydantic
import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlalchemy.orm
import sqlmodel

from app.business.ai import AIExecutionRequirement, AIManager
from app.business.deployment_config import DeploymentConfigManager
from app.business.info_base.relation import RelationManager
from app.business.info_base.resolver import (
  ResolverManager,
  UnknownResolverError,
  UnsupportedResolverCapability,
)
from app.business.peer import PeerManager
from app.engine import SessionLocal
from app.schemas.ai import (
  BlockEmbeddingModel,
  EmbeddingProfileID,
  EmbeddingProfileModel,
  RelationEmbeddingModel,
)
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel
from app.schemas.peer import PeerProtocolRequest, PeerProtocolResponse, PeerRef
from app.schemas.semantic_retrieval import (
  BlockSemanticRetrievalMatch,
  EmbeddingMaintenanceDiagnostic,
  EmbeddingMaintenanceOptions,
  EmbeddingMaintenanceReport,
  RelationSemanticRetrievalMatch,
  SemanticEntityType,
  SemanticRetrievalConfig,
  SemanticRetrievalMatch,
  SemanticRetrievalRequest,
  SemanticRetrievalResult,
  VectorRetrievalOptions,
)


logger = logging.getLogger(__name__)

SEMANTIC_RETRIEVAL_CONFIG_KEY = "semantic_retrieval"
SEMANTIC_RETRIEVAL_CONFIG_SCHEMA = "core.semantic_retrieval.config.v1"
SEMANTIC_RETRIEVAL_CAPABILITY = "core.semantic_retrieval.v1"


class SemanticRetrievalError(RuntimeError):
  pass


class SemanticRetrievalNotConfiguredError(SemanticRetrievalError):
  pass


class EmbeddingProfileNotFoundError(SemanticRetrievalError):
  pass


class InvalidSemanticVectorError(SemanticRetrievalError):
  pass


class SemanticRetrievalDelegationError(SemanticRetrievalError):
  pass


class _ProjectionUnavailable(Exception):
  pass


@dataclass(frozen=True)
class _Candidate:
  entity_type: SemanticEntityType
  entity_id: int
  entity: BlockModel | RelationModel
  text: str


@dataclass(frozen=True)
class _CandidatePage:
  entities: tuple[BlockModel | RelationModel, ...]
  next_cursor: int
  exhausted: bool


@dataclass
class _ReportBuilder:
  profile: EmbeddingProfileID
  diagnostic_limit: int
  embedded: int = 0
  unavailable: int = 0
  failed: int = 0
  diagnostics: list[EmbeddingMaintenanceDiagnostic] | None = None

  def __post_init__(self) -> None:
    self.diagnostics = []

  def record(
    self,
    entity_type: SemanticEntityType,
    entity: int,
    outcome: typing.Literal["unavailable", "failed"],
    reason: str,
  ) -> None:
    if outcome == "unavailable":
      self.unavailable += 1
    else:
      self.failed += 1
    diagnostics = typing.cast(list[EmbeddingMaintenanceDiagnostic], self.diagnostics)
    if len(diagnostics) < self.diagnostic_limit:
      diagnostics.append(
        EmbeddingMaintenanceDiagnostic(
          entity_type=entity_type,
          entity=entity,
          outcome=outcome,
          reason=reason,
        )
      )

  def build(self) -> EmbeddingMaintenanceReport:
    return EmbeddingMaintenanceReport(
      profile=self.profile,
      embedded=self.embedded,
      unavailable=self.unavailable,
      failed=self.failed,
      diagnostics=tuple(self.diagnostics or ()),
    )


DeploymentConfigManager.register_schema(
  SEMANTIC_RETRIEVAL_CONFIG_SCHEMA,
  SemanticRetrievalConfig,
)


class SemanticRetrievalManager:
  """Single use-domain owner for projection, records, ranking and defaults."""

  @classmethod
  def _configured_profile_id(cls) -> EmbeddingProfileID:
    value = DeploymentConfigManager.get(SEMANTIC_RETRIEVAL_CONFIG_KEY)
    if value is None:
      raise SemanticRetrievalNotConfiguredError(
        "Semantic retrieval default Profile is not configured"
      )
    if not isinstance(value, SemanticRetrievalConfig):
      raise TypeError("Semantic retrieval config registry returned the wrong model")
    if value.default_profile is None:
      raise SemanticRetrievalNotConfiguredError(
        "Semantic retrieval default Profile is not configured"
      )
    return value.default_profile

  @classmethod
  def _load_profile(
    cls,
    profile: EmbeddingProfileID | None,
  ) -> EmbeddingProfileModel:
    profile_id = cls._configured_profile_id() if profile is None else profile
    with SessionLocal() as db:
      result = db.get(EmbeddingProfileModel, profile_id)
    if result is None:
      raise EmbeddingProfileNotFoundError(f"Embedding Profile {profile_id} does not exist")
    return result

  @classmethod
  def can_maintain(cls, profile: EmbeddingProfileID | None = None) -> bool:
    """Return static local Job eligibility without probing the provider."""
    try:
      selected = cls._load_profile(profile)
    except (SemanticRetrievalNotConfiguredError, EmbeddingProfileNotFoundError):
      return False
    return AIManager.can_execute(
      selected.ai_model,
      AIExecutionRequirement(
        capability="embedding",
        input_modalities=frozenset({"text"}),
        output_modalities=frozenset({"vector"}),
      ),
    )

  @classmethod
  async def retrieve(
    cls,
    query: str,
    profile: EmbeddingProfileID | None = None,
    options: VectorRetrievalOptions | None = None,
    *,
    route_to_peer: PeerRef | None = None,
  ) -> SemanticRetrievalResult:
    """Execute locally unless the caller explicitly selects another Peer."""
    request = SemanticRetrievalRequest(
      query=query,
      profile=profile,
      options=options or VectorRetrievalOptions(),
    )
    if route_to_peer is None or route_to_peer == PeerManager.get_current_peer_ref():
      return await cls.retrieve_local(
        request.query,
        request.profile,
        request.options,
      )

    payload = PeerProtocolRequest(
      body=typing.cast(
        typing.Any,
        request.model_dump(mode="json"),
      )
    )
    result = await PeerManager.delegate(
      SEMANTIC_RETRIEVAL_CAPABILITY,
      typing.cast(typing.Any, payload.model_dump(mode="json", exclude_unset=True)),
      route_to_peer=route_to_peer,
    )
    try:
      response = PeerProtocolResponse.model_validate(result)
      if response.status != 200 or "body" not in response.model_fields_set:
        raise SemanticRetrievalDelegationError(
          f"Semantic retrieval Peer returned HTTP {response.status}"
        )
      return SemanticRetrievalResult.model_validate(response.body)
    except pydantic.ValidationError as error:
      raise SemanticRetrievalDelegationError(
        "Semantic retrieval Peer returned an invalid response"
      ) from error

  @classmethod
  async def retrieve_local(
    cls,
    query: str,
    profile: EmbeddingProfileID | None = None,
    options: VectorRetrievalOptions | None = None,
  ) -> SemanticRetrievalResult:
    """Execute exact local retrieval without entering Peer delegation."""
    if not query.strip():
      raise ValueError("query must not be empty")
    retrieval_options = options or VectorRetrievalOptions()
    selected = cls._load_profile(profile)
    profile_id = cls._profile_id(selected)
    query_vector = (
      await AIManager.embed(
        selected.ai_model,
        (query,),
        selected.dimensions,
      )
    )[0]
    cls._require_non_zero_vector(query_vector)

    matches: list[SemanticRetrievalMatch] = []
    with SessionLocal() as db:
      if "block" in retrieval_options.entity_types:
        matches.extend(
          cls._retrieve_blocks(
            db,
            selected,
            query_vector,
            retrieval_options,
          )
        )
      if "relation" in retrieval_options.entity_types:
        matches.extend(
          cls._retrieve_relations(
            db,
            selected,
            query_vector,
            retrieval_options,
          )
        )

    matches.sort(
      key=lambda match: (
        -match.score,
        match.type,
        typing.cast(int, match.entity.id),
      )
    )
    return SemanticRetrievalResult(
      profile=profile_id,
      matches=tuple(matches[: retrieval_options.limit]),
    )

  @classmethod
  async def maintain(
    cls,
    profile: EmbeddingProfileID | None = None,
    options: EmbeddingMaintenanceOptions | None = None,
  ) -> EmbeddingMaintenanceReport:
    """Embed only missing/stale records and resume through durable successes."""
    selected = cls._load_profile(profile)
    return await cls._maintain(
      selected,
      options or EmbeddingMaintenanceOptions(),
      rebuild_cutoff=None,
    )

  @classmethod
  async def rebuild(
    cls,
    profile: EmbeddingProfileID | None = None,
    options: EmbeddingMaintenanceOptions | None = None,
  ) -> EmbeddingMaintenanceReport:
    """Re-embed records that were present before this invocation began."""
    selected = cls._load_profile(profile)
    with SessionLocal() as db:
      cutoff = db.exec(sqlmodel.select(sqlalchemy.func.current_timestamp())).one()
    return await cls._maintain(
      selected,
      options or EmbeddingMaintenanceOptions(),
      rebuild_cutoff=cutoff,
    )

  @classmethod
  async def maintain_default(
    cls,
    options: EmbeddingMaintenanceOptions,
  ) -> EmbeddingMaintenanceReport | None:
    """Scheduled no-op when this deployment has no selected default Profile."""
    try:
      return await cls.maintain(options=options)
    except SemanticRetrievalNotConfiguredError:
      return None

  @classmethod
  async def _maintain(
    cls,
    profile: EmbeddingProfileModel,
    options: EmbeddingMaintenanceOptions,
    *,
    rebuild_cutoff: datetime.datetime | None,
  ) -> EmbeddingMaintenanceReport:
    profile_id = cls._profile_id(profile)
    report = _ReportBuilder(profile_id, options.diagnostic_limit)
    batch: list[_Candidate] = []

    async def offer(entity_type: SemanticEntityType, entity) -> bool:
      entity_id = typing.cast(int | None, entity.id)
      if entity_id is None:
        raise RuntimeError("Persisted semantic candidate is missing its ID")
      try:
        text = await cls._project(entity_type, entity)
      except _ProjectionUnavailable as error:
        report.record(entity_type, entity_id, "unavailable", str(error))
        return True
      except Exception as error:
        logger.exception(
          "Semantic projection failed",
          extra={"entity_type": entity_type, "entity": entity_id},
        )
        report.record(entity_type, entity_id, "failed", type(error).__name__)
        return True
      batch.append(_Candidate(entity_type, entity_id, entity, text))
      if (
        len(batch) >= options.batch_size
        or report.embedded + len(batch) >= options.max_embeddings
      ):
        return await flush()
      return True

    async def flush() -> bool:
      if not batch:
        return True
      current = tuple(batch)
      batch.clear()
      try:
        await cls._embed_and_upsert(profile, current)
      except Exception as error:
        logger.exception(
          "Semantic embedding batch failed",
          extra={"profile": profile_id, "batch_size": len(current)},
        )
        for candidate in current:
          report.record(
            candidate.entity_type,
            candidate.entity_id,
            "failed",
            type(error).__name__,
          )
        return False
      report.embedded += len(current)
      return report.embedded < options.max_embeddings

    for entity_type in typing.cast(tuple[SemanticEntityType, ...], ("block", "relation")):
      cursor = 0
      while report.embedded + len(batch) < options.max_embeddings:
        page = cls._candidate_page(
          profile,
          entity_type,
          cursor,
          options.scan_page_size,
          rebuild_cutoff,
        )
        cursor = page.next_cursor
        for entity in page.entities:
          if not await offer(entity_type, entity):
            return report.build()
          if report.embedded >= options.max_embeddings:
            return report.build()
        if page.exhausted:
          break
    await flush()
    return report.build()

  @classmethod
  async def _project(
    cls,
    entity_type: SemanticEntityType,
    entity: BlockModel | RelationModel,
  ) -> str:
    try:
      if entity_type == "block":
        text = await ResolverManager.get(typing.cast(BlockModel, entity)).get_text()
      else:
        text = await RelationManager.get_text(typing.cast(RelationModel, entity))
    except UnknownResolverError as error:
      raise _ProjectionUnavailable("unknown_resolver") from error
    except UnsupportedResolverCapability as error:
      raise _ProjectionUnavailable("unsupported_text") from error
    if text is None or not text.strip():
      raise _ProjectionUnavailable("empty_projection")
    return text

  @classmethod
  async def _embed_and_upsert(
    cls,
    profile: EmbeddingProfileModel,
    candidates: tuple[_Candidate, ...],
  ) -> None:
    vectors = await AIManager.embed(
      profile.ai_model,
      tuple(candidate.text for candidate in candidates),
      profile.dimensions,
    )
    for vector in vectors:
      cls._require_non_zero_vector(vector)

    profile_id = cls._profile_id(profile)
    with SessionLocal() as db:
      for candidate, vector in zip(candidates, vectors, strict=True):
        if candidate.entity_type == "block":
          statement = sqlalchemy.dialects.postgresql.insert(BlockEmbeddingModel).values(
            profile=profile_id,
            block=candidate.entity_id,
            embedding=vector,
          )
          statement = statement.on_conflict_do_update(
            index_elements=["profile", "block"],
            set_={
              "embedding": statement.excluded.embedding,
              "updated_at": sqlalchemy.func.current_timestamp(),
            },
          )
        else:
          statement = sqlalchemy.dialects.postgresql.insert(RelationEmbeddingModel).values(
            profile=profile_id,
            relation=candidate.entity_id,
            embedding=vector,
          )
          statement = statement.on_conflict_do_update(
            index_elements=["profile", "relation"],
            set_={
              "embedding": statement.excluded.embedding,
              "updated_at": sqlalchemy.func.current_timestamp(),
            },
          )
        db.exec(statement)  # type: ignore
      db.commit()

  @classmethod
  def _candidate_page(
    cls,
    profile: EmbeddingProfileModel,
    entity_type: SemanticEntityType,
    cursor: int,
    page_size: int,
    rebuild_cutoff: datetime.datetime | None,
  ) -> _CandidatePage:
    profile_id = cls._profile_id(profile)
    with SessionLocal() as db:
      if entity_type == "block":
        block_columns = typing.cast(
          typing.Any,
          BlockModel.__table__.c,  # pyrefly: ignore[missing-attribute]
        )
        record_columns = typing.cast(
          typing.Any,
          BlockEmbeddingModel.__table__.c,  # pyrefly: ignore[missing-attribute]
        )
        statement = (
          sqlmodel.select(BlockModel, BlockEmbeddingModel)
          .outerjoin(
            BlockEmbeddingModel,
            sqlalchemy.and_(
              record_columns.profile == profile_id,
              record_columns.block == block_columns.id,
            ),
          )
          .where(block_columns.id > cursor)
          .order_by(block_columns.id)
          .limit(page_size)
        )
        rows = db.exec(statement).all()
        entities = tuple(
          block
          for block, record in rows
          if cls._block_requires_embedding(
            profile,
            block,
            record,
            rebuild_cutoff,
          )
        )
        next_cursor = typing.cast(int, rows[-1][0].id) if rows else cursor
        return _CandidatePage(entities, next_cursor, len(rows) < page_size)

      from_block = sqlalchemy.orm.aliased(BlockModel)
      to_block = sqlalchemy.orm.aliased(BlockModel)
      from_columns = typing.cast(typing.Any, from_block)
      to_columns = typing.cast(typing.Any, to_block)
      relation_columns = typing.cast(
        typing.Any,
        RelationModel.__table__.c,  # pyrefly: ignore[missing-attribute]
      )
      record_columns = typing.cast(
        typing.Any,
        RelationEmbeddingModel.__table__.c,  # pyrefly: ignore[missing-attribute]
      )
      statement = (
        sqlmodel.select(
          RelationModel,
          RelationEmbeddingModel,
          from_block.updated_at,
          to_block.updated_at,
        )
        .outerjoin(
          RelationEmbeddingModel,
          sqlalchemy.and_(
            record_columns.profile == profile_id,
            record_columns.relation == relation_columns.id,
          ),
        )
        .join(from_block, from_columns.id == relation_columns.from_)
        .join(to_block, to_columns.id == relation_columns.to_)
        .where(relation_columns.id > cursor)
        .order_by(relation_columns.id)
        .limit(page_size)
      )
      rows = db.exec(statement).all()
      entities = tuple(
        relation
        for relation, record, from_updated_at, to_updated_at in rows
        if cls._relation_requires_embedding(
          profile,
          relation,
          record,
          (from_updated_at, to_updated_at),
          rebuild_cutoff,
        )
      )
      next_cursor = typing.cast(int, rows[-1][0].id) if rows else cursor
      return _CandidatePage(entities, next_cursor, len(rows) < page_size)

  @staticmethod
  def _block_requires_embedding(
    profile: EmbeddingProfileModel,
    block: BlockModel,
    record: BlockEmbeddingModel | None,
    rebuild_cutoff: datetime.datetime | None,
  ) -> bool:
    if record is None:
      return True
    if rebuild_cutoff is not None:
      return record.updated_at < rebuild_cutoff
    return (
      len(record.embedding) != profile.dimensions
      or record.updated_at < profile.updated_at
      or record.updated_at < block.updated_at
    )

  @staticmethod
  def _relation_requires_embedding(
    profile: EmbeddingProfileModel,
    relation: RelationModel,
    record: RelationEmbeddingModel | None,
    endpoint_updated_at: tuple[datetime.datetime, datetime.datetime],
    rebuild_cutoff: datetime.datetime | None,
  ) -> bool:
    if record is None:
      return True
    if rebuild_cutoff is not None:
      return record.updated_at < rebuild_cutoff
    return (
      len(record.embedding) != profile.dimensions
      or record.updated_at < profile.updated_at
      or record.updated_at < relation.updated_at
      or record.updated_at < endpoint_updated_at[0]
      or record.updated_at < endpoint_updated_at[1]
    )

  @classmethod
  def _retrieve_blocks(
    cls,
    db: sqlmodel.Session,
    profile: EmbeddingProfileModel,
    query_vector,
    options: VectorRetrievalOptions,
  ) -> tuple[BlockSemanticRetrievalMatch, ...]:
    profile_id = cls._profile_id(profile)
    block_columns = typing.cast(
      typing.Any,
      BlockModel.__table__.c,  # pyrefly: ignore[missing-attribute]
    )
    record_columns = typing.cast(
      typing.Any,
      BlockEmbeddingModel.__table__.c,  # pyrefly: ignore[missing-attribute]
    )
    distance = record_columns.embedding.cosine_distance(query_vector).label("distance")
    statement = (
      sqlmodel.select(BlockModel, distance)
      .join(BlockEmbeddingModel, record_columns.block == block_columns.id)
      .where(
        record_columns.profile == profile_id,
        record_columns.updated_at >= profile.updated_at,
        record_columns.updated_at >= block_columns.updated_at,
        sqlalchemy.func.vector_dims(record_columns.embedding) == profile.dimensions,
        sqlalchemy.func.vector_norm(record_columns.embedding) > 0,
      )
      .order_by(distance, block_columns.id)
      .limit(options.limit)
    )
    if options.min_score is not None:
      statement = statement.where(distance <= 1 - options.min_score)
    return tuple(
      BlockSemanticRetrievalMatch(
        entity=block,
        score=cls._score(distance_value),
      )
      for block, distance_value in db.exec(statement).all()
    )

  @classmethod
  def _retrieve_relations(
    cls,
    db: sqlmodel.Session,
    profile: EmbeddingProfileModel,
    query_vector,
    options: VectorRetrievalOptions,
  ) -> tuple[RelationSemanticRetrievalMatch, ...]:
    profile_id = cls._profile_id(profile)
    from_block = sqlalchemy.orm.aliased(BlockModel)
    to_block = sqlalchemy.orm.aliased(BlockModel)
    from_columns = typing.cast(typing.Any, from_block)
    to_columns = typing.cast(typing.Any, to_block)
    relation_columns = typing.cast(
      typing.Any,
      RelationModel.__table__.c,  # pyrefly: ignore[missing-attribute]
    )
    record_columns = typing.cast(
      typing.Any,
      RelationEmbeddingModel.__table__.c,  # pyrefly: ignore[missing-attribute]
    )
    distance = record_columns.embedding.cosine_distance(query_vector).label("distance")
    statement = (
      sqlmodel.select(RelationModel, distance)
      .join(
        RelationEmbeddingModel,
        record_columns.relation == relation_columns.id,
      )
      .join(from_block, from_columns.id == relation_columns.from_)
      .join(to_block, to_columns.id == relation_columns.to_)
      .where(
        record_columns.profile == profile_id,
        record_columns.updated_at >= profile.updated_at,
        record_columns.updated_at >= relation_columns.updated_at,
        record_columns.updated_at >= from_columns.updated_at,
        record_columns.updated_at >= to_columns.updated_at,
        sqlalchemy.func.vector_dims(record_columns.embedding) == profile.dimensions,
        sqlalchemy.func.vector_norm(record_columns.embedding) > 0,
      )
      .order_by(distance, relation_columns.id)
      .limit(options.limit)
    )
    if options.min_score is not None:
      statement = statement.where(distance <= 1 - options.min_score)
    return tuple(
      RelationSemanticRetrievalMatch(
        entity=relation,
        score=cls._score(distance_value),
      )
      for relation, distance_value in db.exec(statement).all()
    )

  @staticmethod
  def _profile_id(profile: EmbeddingProfileModel) -> EmbeddingProfileID:
    if profile.id is None:
      raise RuntimeError("Persisted Embedding Profile is missing its ID")
    return profile.id

  @staticmethod
  def _require_non_zero_vector(vector) -> None:
    if not any(value != 0 for value in vector):
      raise InvalidSemanticVectorError("Semantic vectors must be non-zero")

  @staticmethod
  def _score(distance: float) -> float:
    score = 1.0 - distance
    if not math.isfinite(score):
      raise InvalidSemanticVectorError("Cosine score must be finite")
    return min(1.0, max(-1.0, score))
