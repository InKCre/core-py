"""Contracts for exact Organization behaviors and their Agent adapters."""

import typing

import pydantic

from app.schemas.ai import JSONValue
from app.schemas.graph_navigation_retrieval import GraphModel
from app.schemas.info_base.block import BlockID, ResolverType
from app.schemas.info_base.relation import RelationID


class BehaviorAgentConfig(pydantic.BaseModel):
  """Deployment selection of one purpose-built Agent definition."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  agent: int


class AutomaticOrganizationJobParameters(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  max_seeds: int = pydantic.Field(default=10, ge=3, le=100)


class RelationWriteResult(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  relation: RelationID
  created: bool


class CandidateWriteResult(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  descriptor: BlockID
  relation: RelationID
  created: bool


class SupersessionProposal(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  successor_id: BlockID
  predecessor_id: BlockID


class RefinementProposal(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  refinement_id: BlockID
  predecessor_id: BlockID


class EvidenceStanceProposal(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  evidence_id: BlockID
  assertion_id: BlockID
  stance: typing.Literal["supports", "challenges"]


class SynthesisProposal(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  text: str
  source_ids: tuple[BlockID, ...] = pydantic.Field(min_length=2)
  previous_synthesis_id: BlockID | None = None

  @pydantic.field_validator("text")
  @classmethod
  def non_empty_text(cls, value: str) -> str:
    if not value.strip():
      raise ValueError("text must not be empty")
    return value

  @pydantic.field_validator("source_ids")
  @classmethod
  def distinct_sources(cls, value: tuple[BlockID, ...]) -> tuple[BlockID, ...]:
    if len(set(value)) != len(value):
      raise ValueError("source_ids must be distinct")
    return value


class SynthesisWriteResult(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  synthesis: BlockID
  synthesis_created: bool
  basis: tuple[RelationWriteResult, ...]
  edited: RelationWriteResult | None = None


class ExistingReferentAnchorProposal(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  source_id: BlockID
  selected_text: str
  referent_id: BlockID

  @pydantic.field_validator("selected_text")
  @classmethod
  def non_empty_selected_text(cls, value: str) -> str:
    if not value.strip():
      raise ValueError("selected_text must not be empty")
    return value


class ExistingReferentAnchorResult(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  fragment: BlockID
  fragment_created: bool
  has_mention: RelationWriteResult | None
  refers_to: RelationWriteResult


class DuplicateAssertionProposal(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  left_id: BlockID
  right_id: BlockID


class RecordOrganizationCandidateInput(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  information_id: BlockID
  behavior: ResolverType


class SupersessionLineage(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  graph: GraphModel
  current_frontier: tuple[BlockID, ...]
  truncated: bool
  cycle_detected: bool


RetrievalMode: typing.TypeAlias = typing.Literal["lexical", "semantic", "hybrid"]


class OrganizationRetrieveInput(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  query: str
  mode: RetrievalMode = "hybrid"
  limit: int = pydantic.Field(default=20, ge=1, le=20)

  @pydantic.field_validator("query")
  @classmethod
  def non_empty_query(cls, value: str) -> str:
    if not value.strip():
      raise ValueError("query must not be empty")
    return value


class ResolverMethodCall(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  block: BlockID
  method: str
  arguments: dict[str, JSONValue] = pydantic.Field(default_factory=dict)


class ResolverMetaToolInput(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  action: typing.Literal["describe", "invoke"]
  resolvers: tuple[ResolverType, ...] = ()
  blocks: tuple[BlockID, ...] = ()
  calls: tuple[ResolverMethodCall, ...] = pydantic.Field(default=(), max_length=20)

  @pydantic.model_validator(mode="after")
  def valid_action_payload(self) -> typing.Self:
    if self.action == "describe" and self.calls:
      raise ValueError("describe does not accept calls")
    if self.action == "invoke" and (not self.calls or self.resolvers or self.blocks):
      raise ValueError("invoke requires calls and does not accept describe filters")
    return self


class GraphMethodCall(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  method: str
  arguments: dict[str, JSONValue] = pydantic.Field(default_factory=dict)


class GraphRetrievalMetaToolInput(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  action: typing.Literal["describe", "invoke"]
  methods: tuple[str, ...] = ()
  calls: tuple[GraphMethodCall, ...] = pydantic.Field(default=(), max_length=20)

  @pydantic.model_validator(mode="after")
  def valid_action_payload(self) -> typing.Self:
    if self.action == "describe" and self.calls:
      raise ValueError("describe does not accept calls")
    if self.action == "invoke" and (not self.calls or self.methods):
      raise ValueError("invoke requires calls and does not accept method filters")
    return self
