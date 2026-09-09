"""Owner-coherent Agent read tools and exact Organization mutation tools."""

from __future__ import annotations

import asyncio
import dataclasses
import typing

import pydantic

from app.business.agent import AgentManager, ToolExecutionError
from app.business.graph_navigation_retrieval import GraphNavigationRetrievalManager
from app.business.info_base import BlockManager, InfoBaseManager
from app.business.info_base.resolver import (
  ResolverDraftCapability,
  ResolverManager,
)
from app.business.lexical_retrieval import LexicalRetrievalManager
from app.business.semantic_retrieval import SemanticRetrievalManager
from app.schemas.ai import JSONValue
from app.schemas.organization import (
  DraftGraphInput,
  GetDraftGraphSchemaInput,
  SubmitGraphInput,
)
from app.schemas.organization_behavior import (
  DuplicateAssertionProposal,
  EvidenceStanceProposal,
  ExistingReferentAnchorProposal,
  GraphRetrievalMetaToolInput,
  OrganizationRetrieveInput,
  RecordOrganizationCandidateInput,
  RefinementProposal,
  ResolverMetaToolInput,
  SupersessionProposal,
  SynthesisProposal,
)
from ._shared import behavior_resolver_classes, get_behavior_resolver
from .duplicate_assertion import DuplicateAssertionBehaviorResolver
from .evidence_stance import EvidenceStanceBehaviorResolver
from .referent_anchoring import ExistingReferentAnchoringBehaviorResolver
from .refinement import RefinementBehaviorResolver
from .supersession import SupersessionBehaviorResolver
from .synthesis import SynthesisBehaviorResolver


GET_DRAFT_GRAPH_SCHEMA_TOOL = "get_draft_graph_schema"
DRAFT_GRAPH_TOOL = "draft_graph"
SUBMIT_GRAPH_TOOL = "submit_graph"
RETRIEVE_TOOL = "retrieve"
RESOLVER_TOOL = "resolver"
GRAPH_RETRIEVAL_TOOL = "graph_retrieval"
RECORD_SUPERSESSION_TOOL = "record_supersession"
RECORD_REFINEMENT_TOOL = "record_refinement"
RECORD_EVIDENCE_STANCE_TOOL = "record_evidence_stance"
CREATE_SYNTHESIS_TOOL = "create_synthesis"
ANCHOR_EXISTING_REFERENT_TOOL = "anchor_existing_referent"
RECORD_DUPLICATE_ASSERTION_TOOL = "record_duplicate_assertion"
RECORD_ORGANIZATION_CANDIDATE_TOOL = "record_organization_candidate"

_JSON_ADAPTER = pydantic.TypeAdapter(JSONValue)


def _draft_capability_snapshot() -> dict[str, ResolverDraftCapability]:
  return {
    capability.resolver: capability
    for capability in ResolverManager.get_draft_capabilities()
  }


def _schema_discovery_input_model() -> type[pydantic.BaseModel]:
  snapshot = _draft_capability_snapshot()
  if not snapshot:  # pragma: no cover - core.text.v1 is always registered
    raise RuntimeError("No Resolver graph-drafting capability is registered")

  def add_exact_ids(schema: dict[str, typing.Any]) -> None:
    schema["properties"]["resolvers"]["items"] = {
      "type": "string",
      "enum": list(snapshot),
    }

  class BoundGetDraftGraphSchemaInput(GetDraftGraphSchemaInput):
    model_config = pydantic.ConfigDict(
      extra="forbid",
      frozen=True,
      json_schema_extra=add_exact_ids,
    )

    @pydantic.field_validator("resolvers")
    @classmethod
    def exact_resolvers(cls, resolvers: tuple[str, ...]) -> tuple[str, ...]:
      unknown = tuple(resolver for resolver in resolvers if resolver not in snapshot)
      if unknown:
        raise ValueError(f"Unavailable draft Resolver IDs: {unknown!r}")
      return resolvers

  return BoundGetDraftGraphSchemaInput


def _draft_graph_input_model() -> type[pydantic.BaseModel]:
  snapshot = _draft_capability_snapshot()
  if not snapshot:  # pragma: no cover - core.text.v1 is always registered
    raise RuntimeError("No Resolver graph-drafting capability is registered")

  def add_exact_ids(schema: dict[str, typing.Any]) -> None:
    schema["properties"]["resolver"] = {
      "type": "string",
      "enum": list(snapshot),
    }

  class BoundDraftGraphInput(DraftGraphInput):
    model_config = pydantic.ConfigDict(
      extra="forbid",
      json_schema_extra=add_exact_ids,
    )

    @pydantic.field_validator("resolver")
    @classmethod
    def exact_resolver(cls, resolver: str) -> str:
      if resolver not in snapshot:
        raise ValueError(f"Unavailable draft Resolver ID: {resolver!r}")
      return resolver

    @pydantic.model_validator(mode="after")
    def validate_resolver_input(self) -> typing.Self:
      capability = snapshot[self.resolver]
      resolver_input = capability.input_model.model_validate(self.input)
      object.__setattr__(self, "_resolver_input", resolver_input)
      return self

  return BoundDraftGraphInput


@AgentManager.tool(
  GET_DRAFT_GRAPH_SCHEMA_TOOL,
  description="Return code-owned draft-input JSON Schemas for exact Resolver IDs.",
  input_model_factory=_schema_discovery_input_model,
)
async def get_draft_graph_schema(input: GetDraftGraphSchemaInput) -> JSONValue:
  snapshot = _draft_capability_snapshot()
  return {
    "resolvers": [
      {
        "resolver": resolver,
        "description": snapshot[resolver].description,
        "input_schema": typing.cast(
          dict[str, JSONValue],
          snapshot[resolver].input_model.model_json_schema(),
        ),
      }
      for resolver in input.resolvers
    ]
  }


@AgentManager.tool(
  DRAFT_GRAPH_TOOL,
  description="Draft one rooted GraphForm through an exact Resolver without persistence.",
  input_model_factory=_draft_graph_input_model,
)
async def draft_graph(input: DraftGraphInput) -> JSONValue:
  capability = ResolverManager.get_draft_capability(input.resolver)
  resolver_input = typing.cast(pydantic.BaseModel, getattr(input, "_resolver_input"))
  stars = capability.resolver_cls.create_graph(resolver_input)
  graph = InfoBaseManager.normalize_graph(stars, input.id_start)
  return typing.cast(JSONValue, graph.model_dump(mode="json"))


@AgentManager.tool(
  SUBMIT_GRAPH_TOOL,
  description="Persist one complete GraphForm and return local-to-persisted Block IDs.",
)
async def submit_graph(input: SubmitGraphInput) -> JSONValue:
  result = InfoBaseManager.submit_graph(input.graph)
  return typing.cast(JSONValue, result.model_dump(mode="json"))


@AgentManager.tool(
  RETRIEVE_TOOL,
  description="Retrieve lexical, semantic, or separate hybrid results for one query.",
)
async def retrieve(input: OrganizationRetrieveInput) -> JSONValue:
  async def lexical() -> JSONValue:
    result = await asyncio.to_thread(
      LexicalRetrievalManager.retrieve_local,
      input.query,
      input.limit,
    )
    return typing.cast(JSONValue, result.model_dump(mode="json"))

  async def semantic() -> JSONValue:
    from app.schemas.semantic_retrieval import VectorRetrievalOptions

    result = await SemanticRetrievalManager.retrieve_local(
      input.query,
      options=VectorRetrievalOptions(limit=input.limit),
    )
    return typing.cast(JSONValue, result.model_dump(mode="json"))

  branches = (
    ("lexical", lexical),
    ("semantic", semantic),
  )
  selected = (
    branches
    if input.mode == "hybrid"
    else tuple(branch for branch in branches if branch[0] == input.mode)
  )
  outcomes = await asyncio.gather(
    *(operation() for _, operation in selected),
    return_exceptions=True,
  )
  return {
    name: (
      {"error": type(outcome).__name__, "message": str(outcome)}
      if isinstance(outcome, BaseException)
      else outcome
    )
    for (name, _), outcome in zip(selected, outcomes, strict=True)
  }


@AgentManager.tool(
  RESOLVER_TOOL,
  description="Describe or invoke public typed read methods on exact Block Resolvers.",
)
async def resolver(input: ResolverMetaToolInput) -> JSONValue:
  if input.action == "describe":
    found = await asyncio.to_thread(BlockManager.get_many, input.blocks)
    resolver_ids = set(input.resolvers)
    resolver_ids.update(block.resolver for block in found)
    if not resolver_ids:
      resolver_ids.update(ResolverManager.RESOLVER_CLS)
    return typing.cast(
      JSONValue,
      {
        "results": [
          {
            "resolver": resolver_id,
            "methods": [
              {
                "name": contract.name,
                "description": contract.description,
                "input_schema": contract.input_schema,
              }
              for contract in ResolverManager.get_method_contracts(resolver_id)
            ],
          }
          for resolver_id in sorted(resolver_ids)
          if resolver_id in ResolverManager.RESOLVER_CLS
        ],
        "missing_blocks": sorted(set(input.blocks) - {block.id for block in found}),
        "missing_resolvers": sorted(
          resolver_id
          for resolver_id in resolver_ids
          if resolver_id not in ResolverManager.RESOLVER_CLS
        ),
      },
    )

  results: list[JSONValue] = []
  for index, call in enumerate(input.calls):
    block = await asyncio.to_thread(BlockManager.get, call.block)
    if block is None:
      results.append(
        {"index": index, "block": call.block, "method": call.method, "error": "not_found"}
      )
      continue
    try:
      value = await ResolverManager.invoke_method(
        block,
        call.method,
        typing.cast(dict[str, typing.Any], call.arguments),
      )
      projected = _project_json(value)
    except Exception as error:
      results.append(
        {
          "index": index,
          "block": call.block,
          "method": call.method,
          "error": type(error).__name__,
          "message": str(error),
        }
      )
    else:
      results.append(
        {
          "index": index,
          "block": call.block,
          "method": call.method,
          "result": projected,
        }
      )
  return typing.cast(JSONValue, {"results": results})


@AgentManager.tool(
  GRAPH_RETRIEVAL_TOOL,
  description="Describe or invoke public typed bounded Graph Navigation queries.",
)
async def graph_retrieval(input: GraphRetrievalMetaToolInput) -> JSONValue:
  contracts = GraphNavigationRetrievalManager.get_query_contracts()
  if input.action == "describe":
    selected = set(input.methods)
    return typing.cast(
      JSONValue,
      {
        "methods": [
          {
            "name": contract.name,
            "description": contract.description,
            "input_schema": contract.input_schema,
          }
          for contract in contracts
          if not selected or contract.name in selected
        ],
        "missing_methods": sorted(selected - {contract.name for contract in contracts}),
      },
    )

  results: list[JSONValue] = []
  for index, call in enumerate(input.calls):
    try:
      value = await asyncio.to_thread(
        GraphNavigationRetrievalManager.invoke_query,
        call.method,
        typing.cast(dict[str, typing.Any], call.arguments),
      )
      projected = _project_json(value)
    except Exception as error:
      results.append(
        {
          "index": index,
          "method": call.method,
          "error": type(error).__name__,
          "message": str(error),
        }
      )
    else:
      results.append({"index": index, "method": call.method, "result": projected})
  return typing.cast(JSONValue, {"results": results})


def _candidate_input_model() -> type[pydantic.BaseModel]:
  snapshot = {behavior.__rsotype__: behavior for behavior in behavior_resolver_classes()}
  if not snapshot:
    raise RuntimeError("No Organization Behavior Resolver is registered")

  def add_exact_behaviors(schema: dict[str, typing.Any]) -> None:
    schema["properties"]["behavior"] = {
      "oneOf": [
        {
          "const": behavior_id,
          "description": behavior.organization_description,
        }
        for behavior_id, behavior in snapshot.items()
      ]
    }

  class BoundRecordOrganizationCandidateInput(RecordOrganizationCandidateInput):
    model_config = pydantic.ConfigDict(
      extra="forbid",
      frozen=True,
      json_schema_extra=add_exact_behaviors,
    )

    @pydantic.field_validator("behavior")
    @classmethod
    def exact_behavior(cls, behavior: str) -> str:
      if behavior not in snapshot:
        raise ValueError(f"Unavailable Organization behavior: {behavior!r}")
      return behavior

  return BoundRecordOrganizationCandidateInput


async def _exact_result(operation: typing.Awaitable[pydantic.BaseModel]) -> JSONValue:
  try:
    result = await operation
  except (ValueError, RuntimeError) as error:
    raise ToolExecutionError(
      {"error": type(error).__name__, "message": str(error)}
    ) from error
  return typing.cast(JSONValue, result.model_dump(mode="json"))


@AgentManager.tool(
  RECORD_SUPERSESSION_TOOL,
  description="Persist one exact successor --supersedes--> predecessor relation.",
)
async def record_supersession(input: SupersessionProposal) -> JSONValue:
  return await _exact_result(
    SupersessionBehaviorResolver.record_supersession(
      input.successor_id,
      input.predecessor_id,
    )
  )


@AgentManager.tool(
  RECORD_REFINEMENT_TOOL,
  description="Persist one exact refinement --refines--> predecessor relation.",
)
async def record_refinement(input: RefinementProposal) -> JSONValue:
  return await _exact_result(
    RefinementBehaviorResolver.record_refinement(
      input.refinement_id,
      input.predecessor_id,
    )
  )


@AgentManager.tool(
  RECORD_EVIDENCE_STANCE_TOOL,
  description="Persist one attributable evidence support or challenge relation.",
)
async def record_evidence_stance(input: EvidenceStanceProposal) -> JSONValue:
  return await _exact_result(
    EvidenceStanceBehaviorResolver.record_evidence_stance(
      input.evidence_id,
      input.assertion_id,
      input.stance,
    )
  )


@AgentManager.tool(
  CREATE_SYNTHESIS_TOOL,
  description="Create or replay one provenance-preserving multi-source synthesis.",
)
async def create_synthesis(input: SynthesisProposal) -> JSONValue:
  return await _exact_result(
    SynthesisBehaviorResolver.create_synthesis(
      input.text,
      input.source_ids,
      input.previous_synthesis_id,
    )
  )


@AgentManager.tool(
  ANCHOR_EXISTING_REFERENT_TOOL,
  description="Anchor a source-grounded selected-text fragment to an existing referent.",
)
async def anchor_existing_referent(
  input: ExistingReferentAnchorProposal,
) -> JSONValue:
  return await _exact_result(
    ExistingReferentAnchoringBehaviorResolver.anchor_existing_referent(
      input.source_id,
      input.selected_text,
      input.referent_id,
    )
  )


@AgentManager.tool(
  RECORD_DUPLICATE_ASSERTION_TOOL,
  description="Persist one whole-Block duplicate assertion from one provenance occurrence.",
)
async def record_duplicate_assertion(input: DuplicateAssertionProposal) -> JSONValue:
  return await _exact_result(
    DuplicateAssertionBehaviorResolver.record_duplicate_assertion(
      input.left_id,
      input.right_id,
    )
  )


@AgentManager.tool(
  RECORD_ORGANIZATION_CANDIDATE_TOOL,
  description="Cautiously mark information for one exact registered Organization behavior.",
  input_model_factory=_candidate_input_model,
)
async def record_organization_candidate(
  input: RecordOrganizationCandidateInput,
) -> JSONValue:
  behavior = get_behavior_resolver(input.behavior)
  if behavior is None:
    raise ToolExecutionError({"error": "behavior_unavailable"})
  return await _exact_result(
    typing.cast(typing.Any, behavior).record_candidate(input.information_id)
  )


def _project_json(value: typing.Any) -> JSONValue:
  if _contains_bytes(value):
    raise TypeError("Binary Resolver values are unavailable through this Agent Tool")
  if isinstance(value, pydantic.BaseModel):
    projected = value.model_dump(mode="json")
  elif dataclasses.is_dataclass(value) and not isinstance(value, type):
    projected = dataclasses.asdict(value)
  else:
    projected = pydantic.TypeAdapter(typing.Any).dump_python(
      typing.cast(typing.Any, value),
      mode="json",
    )
  return _JSON_ADAPTER.validate_python(projected)


def _contains_bytes(value: typing.Any) -> bool:
  if isinstance(value, bytes):
    return True
  if isinstance(value, pydantic.BaseModel):
    return any(
      _contains_bytes(getattr(value, field)) for field in value.__class__.model_fields
    )
  if dataclasses.is_dataclass(value) and not isinstance(value, type):
    return any(
      _contains_bytes(getattr(value, field.name)) for field in dataclasses.fields(value)
    )
  if isinstance(value, dict):
    return any(_contains_bytes(item) for item in value.values())
  if isinstance(value, list | tuple | set | frozenset):
    return any(_contains_bytes(item) for item in value)
  return False
