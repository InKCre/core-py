"""Contracts for exact Organization behaviors and their Agent adapters."""

import typing

import pydantic

from app.schemas.ai import JSONValue
from app.schemas.graph_navigation_retrieval import (
  GraphDirection,
  GraphModel,
  DEFAULT_NEIGHBORHOOD_LIMIT,
  MAX_NEIGHBORHOOD_LIMIT,
  DEFAULT_MAX_HOPS,
  MAX_MAX_HOPS,
  DEFAULT_MAX_EXPLORED_BLOCKS,
  MAX_MAX_EXPLORED_BLOCKS,
  DEFAULT_MAX_EXPLORED_RELATIONS,
)
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

  relation_id: RelationID
  created: bool


class CandidateWriteResult(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  descriptor_block_id: BlockID
  relation_id: RelationID
  created: bool


class SupersessionProposal(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  successor_block_id: BlockID
  predecessor_block_id: BlockID


class RefinementProposal(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  refinement_block_id: BlockID
  predecessor_block_id: BlockID


class EvidenceStanceProposal(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  evidence_block_id: BlockID
  assertion_block_id: BlockID
  stance: typing.Literal["supports", "challenges"]


class SynthesisProposal(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  text: str
  source_block_ids: tuple[BlockID, ...] = pydantic.Field(
    min_length=2, description="Actual contributing sources, not all inspected context."
  )
  previous_synthesis_block_id: BlockID | None = pydantic.Field(
    default=None, description="Earlier synthesis revised through an edited relation."
  )

  @pydantic.field_validator("text")
  @classmethod
  def non_empty_text(cls, value: str) -> str:
    if not value.strip():
      raise ValueError("text must not be empty")
    return value

  @pydantic.field_validator("source_block_ids")
  @classmethod
  def distinct_sources(cls, value: tuple[BlockID, ...]) -> tuple[BlockID, ...]:
    if len(set(value)) != len(value):
      raise ValueError("source_block_ids must be distinct")
    return value


class SynthesisWriteResult(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  synthesis_block_id: BlockID
  synthesis_created: bool
  basis: tuple[RelationWriteResult, ...]
  edited: RelationWriteResult | None = None


class ExistingReferentAnchorProposal(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  source_block_id: BlockID
  selected_text: str = pydantic.Field(
    description="Minimal sufficient referring fragment from the source."
  )
  referent_block_id: BlockID

  @pydantic.field_validator("selected_text")
  @classmethod
  def non_empty_selected_text(cls, value: str) -> str:
    if not value.strip():
      raise ValueError("selected_text must not be empty")
    return value


class ExistingReferentAnchorResult(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  fragment_block_id: BlockID
  fragment_created: bool
  has_mention: RelationWriteResult | None
  refers_to: RelationWriteResult


class DuplicateAssertionProposal(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  left_block_id: BlockID
  right_block_id: BlockID


class RecordOrganizationCandidateInput(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  block_id: BlockID
  behavior: ResolverType


class SupersessionLineage(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  graph: GraphModel
  current_block_ids: tuple[BlockID, ...]
  truncated: bool
  cycle_detected: bool


RetrievalMode: typing.TypeAlias = typing.Literal["lexical", "semantic", "hybrid"]


class OrganizationRetrieveInput(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  query: str = pydantic.Field(description="Search terms or a semantic description.")
  mode: RetrievalMode = "hybrid"
  limit: int = pydantic.Field(
    default=20, ge=1, le=20, description="Maximum matches per mode."
  )

  @pydantic.field_validator("query")
  @classmethod
  def non_empty_query(cls, value: str) -> str:
    if not value.strip():
      raise ValueError("query must not be empty")
    return value


class ResolverMethodCall(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  block_id: BlockID
  method: str
  arguments: dict[str, JSONValue] = pydantic.Field(default_factory=dict)


class ResolverDescribeInput(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  action: typing.Literal["describe"]
  resolver_types: tuple[ResolverType, ...] = ()
  block_ids: tuple[BlockID, ...] = ()
  calls: tuple[ResolverMethodCall, ...] = pydantic.Field(default=(), max_length=0)


class ResolverInvokeInput(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  action: typing.Literal["invoke"]
  resolver_types: tuple[ResolverType, ...] = pydantic.Field(default=(), max_length=0)
  block_ids: tuple[BlockID, ...] = pydantic.Field(default=(), max_length=0)
  calls: tuple[ResolverMethodCall, ...] = pydantic.Field(min_length=1, max_length=20)


class ResolverMetaToolInput(
  pydantic.RootModel[
    typing.Annotated[
      ResolverDescribeInput | ResolverInvokeInput, pydantic.Field(discriminator="action")
    ]
  ]
):
  pass


class GetEntitiesInput(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  entity_type: typing.Literal["block", "relation"] = "block"
  entity_ids: tuple[int, ...] = pydantic.Field(
    default=(),
    max_length=20,
    description="Ordered results; missing IDs return null. Empty selects random Blocks.",
  )
  random_count: int = pydantic.Field(
    default=1,
    ge=1,
    le=20,
    description="Maximum distinct random Blocks when entity_ids is empty.",
  )

  @pydantic.model_validator(mode="after")
  def validate_selection(self) -> typing.Self:
    if self.entity_type == "relation" and not self.entity_ids:
      raise ValueError("Relations require entity_ids")
    if self.entity_ids and self.random_count != 1:
      raise ValueError("random_count only applies when entity_ids is empty")
    return self


class BlockNeighborhoodInput(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  entity_type: typing.Literal["block"]
  entity_id: BlockID
  direction: GraphDirection = "both"
  contents: tuple[str, ...] = pydantic.Field(
    default=(), description="Exact Relation contents; empty means all."
  )
  limit: int = pydantic.Field(
    default=DEFAULT_NEIGHBORHOOD_LIMIT, ge=1, le=MAX_NEIGHBORHOOD_LIMIT
  )
  cursor: RelationID | None = pydantic.Field(
    default=None, description="Previous next_cursor."
  )


class RelationNeighborhoodInput(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  entity_type: typing.Literal["relation"]
  entity_id: RelationID


class EntityNeighborhoodInput(
  pydantic.RootModel[
    typing.Annotated[
      BlockNeighborhoodInput | RelationNeighborhoodInput,
      pydantic.Field(discriminator="entity_type"),
    ]
  ]
):
  model_config = pydantic.ConfigDict(json_schema_extra={"type": "object"})

  @classmethod
  def model_json_schema(cls, *args, **kwargs) -> dict[str, typing.Any]:
    schema = super().model_json_schema(*args, **kwargs)
    properties = BlockNeighborhoodInput.model_json_schema(*args, **kwargs)["properties"]
    properties["entity_type"] = {
      "type": "string",
      "enum": [
        typing.get_args(branch.model_fields["entity_type"].annotation)[0]
        for branch in (BlockNeighborhoodInput, RelationNeighborhoodInput)
      ],
    }
    schema["properties"] = properties
    return schema


class FindPathInput(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  from_block_id: BlockID
  to_block_id: BlockID
  direction: GraphDirection = "both"
  contents: tuple[str, ...] = pydantic.Field(
    default=(), description="Exact Relation contents; empty means all."
  )
  max_hops: int = pydantic.Field(default=DEFAULT_MAX_HOPS, ge=0, le=MAX_MAX_HOPS)
  max_explored_blocks: int = pydantic.Field(
    default=DEFAULT_MAX_EXPLORED_BLOCKS, ge=1, le=MAX_MAX_EXPLORED_BLOCKS
  )


class ConnectedComponentsInput(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  seed_block_ids: tuple[BlockID, ...]
  contents: tuple[str, ...] = pydantic.Field(
    min_length=1, description="Exact Relation contents treated as undirected connections."
  )
  max_explored_blocks: int = pydantic.Field(default=DEFAULT_MAX_EXPLORED_BLOCKS, ge=1)
  max_explored_relations: int = pydantic.Field(default=DEFAULT_MAX_EXPLORED_RELATIONS, ge=1)
