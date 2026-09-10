"""Owner-coherent Agent read tools and exact Organization mutation tools."""

from __future__ import annotations

import asyncio
import dataclasses
import typing

import pydantic

from app.business.agent import AgentManager, ToolExecutionError
from app.business.graph_navigation_retrieval import GraphNavigationRetrievalManager
from app.business.info_base import BlockManager, InfoBaseManager, RelationManager
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
  GetEntityInput,
  EntityNeighborhoodInput,
  FindPathInput,
  ConnectedComponentsInput,
  OrganizationRetrieveInput,
  RecordOrganizationCandidateInput,
  RefinementProposal,
  ResolverMetaToolInput,
  ResolverDescribeInput,
  ResolverInvokeInput,
  ResolverMethodCall,
  SupersessionProposal,
  SynthesisProposal,
)
from ._shared import behavior_resolver_classes, get_behavior_resolver
from .contracts import OrganizationError
from .duplicate_assertion import (
  DUPLICATES_ASSERTION_RELATION,
  DuplicateAssertionBehaviorResolver,
)
from .evidence_stance import EvidenceStanceBehaviorResolver
from .referent_anchoring import ExistingReferentAnchoringBehaviorResolver
from .refinement import REFINES_RELATION, RefinementBehaviorResolver
from .supersession import SUPERSEDES_RELATION, SupersessionBehaviorResolver
from .synthesis import SynthesisBehaviorResolver


GET_DRAFT_GRAPH_SCHEMA_TOOL = "get_draft_graph_schema"
DRAFT_GRAPH_TOOL = "draft_graph"
SUBMIT_GRAPH_TOOL = "submit_graph"
RETRIEVE_TOOL = "retrieve"
RESOLVER_TOOL = "resolver"
GET_ENTITY_TOOL = "get_entity"
GET_ENTITY_NEIGHBORHOOD_TOOL = "get_entity_neighborhood"
FIND_PATH_TOOL = "find_path"
GET_CONNECTED_COMPONENTS_TOOL = "get_connected_components"
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
    schema["properties"]["resolver_types"]["items"] = {
      "type": "string",
      "enum": list(snapshot),
    }

  class BoundGetDraftGraphSchemaInput(GetDraftGraphSchemaInput):
    model_config = pydantic.ConfigDict(
      extra="forbid",
      frozen=True,
      json_schema_extra=add_exact_ids,
    )

    @pydantic.field_validator("resolver_types")
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
    schema["properties"]["resolver_type"] = {
      "type": "string",
      "enum": list(snapshot),
    }

  class BoundDraftGraphInput(DraftGraphInput):
    model_config = pydantic.ConfigDict(
      extra="forbid",
      json_schema_extra=add_exact_ids,
    )

    @pydantic.field_validator("resolver_type")
    @classmethod
    def exact_resolver(cls, resolver: str) -> str:
      if resolver not in snapshot:
        raise ValueError(f"Unavailable draft Resolver ID: {resolver!r}")
      return resolver

    @pydantic.model_validator(mode="after")
    def validate_resolver_input(self) -> typing.Self:
      capability = snapshot[self.resolver_type]
      # Validate at the caller's actual path; an inner resolver_type error must
      # not tell the Agent to remove its valid outer selector.
      payload_model = pydantic.create_model(
        "ResolverDraftPayload", input=(capability.input_model, ...)
      )
      payload = payload_model.model_validate({"input": self.input})
      object.__setattr__(self, "_resolver_input", getattr(payload, "input"))
      return self

  return BoundDraftGraphInput


@AgentManager.tool(
  GET_DRAFT_GRAPH_SCHEMA_TOOL,
  description="Describe graph-drafting inputs for selected Resolver types.",
  input_model_factory=_schema_discovery_input_model,
)
async def get_draft_graph_schema(input: GetDraftGraphSchemaInput) -> JSONValue:
  snapshot = _draft_capability_snapshot()
  return {
    "resolvers": [
      {
        "resolver_type": resolver,
        "description": snapshot[resolver].description,
        "input_schema": typing.cast(
          dict[str, JSONValue],
          snapshot[resolver].input_model.model_json_schema(),
        ),
      }
      for resolver in input.resolver_types
    ]
  }


@AgentManager.tool(
  DRAFT_GRAPH_TOOL,
  description="Draft one rooted GraphForm through an exact Resolver without persistence.",
  input_model_factory=_draft_graph_input_model,
)
async def draft_graph(input: DraftGraphInput) -> JSONValue:
  capability = ResolverManager.get_draft_capability(input.resolver_type)
  resolver_input = typing.cast(pydantic.BaseModel, getattr(input, "_resolver_input"))
  stars = capability.resolver_cls.create_graph(resolver_input)
  graph = InfoBaseManager.normalize_graph(stars, input.local_block_id_start)
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
    return typing.cast(
      JSONValue,
      {
        "matches": [
          {
            "entity": {"entity_type": "block", "entity_id": match.block.id},
            **match.model_dump(mode="json", exclude={"block"}),
          }
          for match in result.matches
        ]
      },
    )

  async def semantic() -> JSONValue:
    from app.schemas.semantic_retrieval import VectorRetrievalOptions

    result = await SemanticRetrievalManager.retrieve_local(
      input.query,
      options=VectorRetrievalOptions(limit=input.limit),
    )
    return typing.cast(
      JSONValue,
      {
        **result.model_dump(mode="json", exclude={"matches"}),
        "matches": [
          {
            "entity": {"entity_type": match.type, "entity_id": match.entity.id},
            "score": match.score,
          }
          for match in result.matches
        ],
      },
    )

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


def _resolver_input_model() -> type[pydantic.BaseModel]:
  common = ResolverManager.get_common_method_contracts()
  variants: list[type[pydantic.BaseModel]] = []
  contracts = list(common)
  for resolver_type in ResolverManager.RESOLVER_CLS:
    contracts.extend(
      contract
      for contract in ResolverManager.get_method_contracts(resolver_type)
      if contract.name in {item.name for item in common}
    )
  seen: set[tuple] = set()
  for contract in contracts:
    signature = (
      contract.name,
      tuple(
        (name, repr(field.annotation), repr(field.default), repr(field.metadata))
        for name, field in contract.input_model.model_fields.items()
      ),
    )
    if signature in seen:
      continue
    seen.add(signature)
    variants.append(
      pydantic.create_model(
        f"{contract.name}_Call_{len(variants)}",
        __config__=pydantic.ConfigDict(extra="forbid"),
        block_id=(int, ...),
        method=(
          typing.cast(typing.Any, typing.Literal)[contract.name],
          pydantic.Field(description=contract.description),
        ),
        arguments=(
          contract.input_model,
          ...
          if any(
            field.is_required() for field in contract.input_model.model_fields.values()
          )
          else pydantic.Field(default_factory=contract.input_model),
        ),
      )
    )

  variants.append(
    pydantic.create_model(
      "ExtraMethodCall",
      __base__=ResolverMethodCall,
      method=(
        str,
        pydantic.Field(
          json_schema_extra={"not": {"enum": [contract.name for contract in common]}}
        ),
      ),
    )
  )
  call_type = typing.cast(typing.Any, typing.Union)[tuple(variants)]
  invoke = pydantic.create_model(
    "BoundResolverInvokeInput",
    __base__=ResolverInvokeInput,
    calls=(tuple[call_type, ...], pydantic.Field(min_length=1, max_length=20)),
  )
  envelope = pydantic.create_model(
    "ResolverEnvelope",
    __base__=ResolverDescribeInput,
    action=(typing.Literal["describe", "invoke"], ...),
    calls=(tuple[call_type, ...], pydantic.Field(default=(), max_length=20)),
  )

  documented = pydantic.RootModel[
    typing.Annotated[ResolverDescribeInput | invoke, pydantic.Field(discriminator="action")]
  ]

  class BoundResolverInput(ResolverMetaToolInput):
    @classmethod
    def model_json_schema(cls, *args, **kwargs) -> dict[str, typing.Any]:
      # Method arguments are validated once by their actual Resolver owner, per
      # call. A bad method argument must not discard successful batch siblings.
      schema = documented.model_json_schema(*args, **kwargs)
      # Some providers infer parameter types only from top-level properties.
      # The union owns conditional validation; this is its wider envelope.
      visible = envelope.model_json_schema(*args, **kwargs)
      schema.update(type="object", properties=visible["properties"])
      schema.setdefault("$defs", {}).update(visible.get("$defs", {}))
      return schema

  return BoundResolverInput


@AgentManager.tool(
  RESOLVER_TOOL,
  input_model_factory=_resolver_input_model,
  description="Describe or invoke public typed read methods on exact Block Resolvers.",
)
async def resolver(input: ResolverMetaToolInput) -> JSONValue:
  request = input.root
  if request.action == "describe":
    found = await asyncio.to_thread(BlockManager.get_many, request.block_ids)
    resolver_ids = set(request.resolver_types)
    resolver_ids.update(block.resolver for block in found)
    if not request.block_ids and not request.resolver_types:
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
        "missing_blocks": sorted(set(request.block_ids) - {block.id for block in found}),
        "missing_resolvers": sorted(
          resolver_id
          for resolver_id in resolver_ids
          if resolver_id not in ResolverManager.RESOLVER_CLS
        ),
      },
    )

  results: list[JSONValue] = []
  for index, call in enumerate(request.calls):
    block = await asyncio.to_thread(BlockManager.get, call.block_id)
    if block is None:
      results.append(
        {
          "index": index,
          "block_id": call.block_id,
          "method": call.method,
          "error": "not_found",
        }
      )
      continue
    contract = ResolverManager.get_method_contract(block.resolver, call.method)
    if block.resolver not in ResolverManager.RESOLVER_CLS:
      results.append(
        {
          "index": index,
          "block_id": call.block_id,
          "method": call.method,
          "error": "resolver_unavailable",
          "message": f"Resolver {block.resolver!r} is not registered.",
        }
      )
      continue
    if contract is None:
      results.append(
        {
          "index": index,
          "block_id": call.block_id,
          "method": call.method,
          "error": "method_unavailable",
          "message": "Method does not exist; use describe for available method contracts.",
          "available_methods": [
            item.name for item in ResolverManager.get_method_contracts(block.resolver)
          ],
        }
      )
      continue
    try:
      value = await ResolverManager.invoke_method(
        block,
        call.method,
        call.arguments.model_dump()
        if isinstance(call.arguments, pydantic.BaseModel)
        else typing.cast(dict[str, typing.Any], call.arguments),
      )
      projected = _project_json(value)
    except pydantic.ValidationError as error:
      results.append(
        typing.cast(
          JSONValue,
          {
            "index": index,
            "block_id": call.block_id,
            "method": call.method,
            "error": "invalid_arguments",
            "fields": error.errors(
              include_url=False, include_context=False, include_input=False
            ),
            "input_schema": contract.input_schema,
          },
        )
      )
    except Exception as error:
      results.append(
        {
          "index": index,
          "block_id": call.block_id,
          "method": call.method,
          "error": type(error).__name__,
          "message": str(error),
        }
      )
    else:
      results.append(
        {
          "index": index,
          "block_id": call.block_id,
          "method": call.method,
          "result": projected,
        }
      )
  return typing.cast(JSONValue, {"results": results})


@AgentManager.tool(
  GET_ENTITY_TOOL,
  description="Read a persisted Block or Relation without resolving its content.",
)
async def get_entity(input: GetEntityInput) -> JSONValue:
  if input.entity_type == "block":
    entity = (
      await asyncio.to_thread(BlockManager.get_random)
      if input.entity_id is None
      else await asyncio.to_thread(BlockManager.get, input.entity_id)
    )
  else:
    assert input.entity_id is not None
    entity = await asyncio.to_thread(RelationManager.get_by_id, input.entity_id)
  return _project_json(entity)


@AgentManager.tool(
  GET_ENTITY_NEIGHBORHOOD_TOOL,
  description="Read a Block's direct neighborhood or a Relation with its endpoints.",
)
async def get_entity_neighborhood(input: EntityNeighborhoodInput) -> JSONValue:
  request = input.root
  if request.entity_type == "block":
    result = await asyncio.to_thread(
      GraphNavigationRetrievalManager.get_block_neighborhood,
      request.entity_id,
      direction=request.direction,
      contents=request.contents,
      limit=request.limit,
      cursor=request.cursor,
    )
  else:
    result = await asyncio.to_thread(
      GraphNavigationRetrievalManager.get_relation_neighborhood,
      request.entity_id,
    )
  return _project_json(result)


@AgentManager.tool(
  FIND_PATH_TOOL,
  description="Find a bounded graph path; an exploration limit is not proof of absence.",
)
async def find_path(input: FindPathInput) -> JSONValue:
  result = await asyncio.to_thread(
    GraphNavigationRetrievalManager.find_path,
    input.from_block_id,
    input.to_block_id,
    direction=input.direction,
    contents=input.contents,
    max_hops=input.max_hops,
    max_explored_blocks=input.max_explored_blocks,
  )
  return _project_json(result)


@AgentManager.tool(
  GET_CONNECTED_COMPONENTS_TOOL,
  description=(
    "Partition seeds by bounded undirected reachability through exact Relation contents."
  ),
)
async def get_connected_components(input: ConnectedComponentsInput) -> JSONValue:
  return await _exact_result(
    asyncio.to_thread(
      GraphNavigationRetrievalManager.get_connected_components,
      **input.model_dump(),
    )
  )


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
        raise ValueError(
          f"Unavailable behavior {behavior!r}; available: {', '.join(snapshot)}"
        )
      return behavior

  return BoundRecordOrganizationCandidateInput


async def _exact_result(operation: typing.Awaitable[pydantic.BaseModel]) -> JSONValue:
  try:
    result = await operation
  except (ValueError, OrganizationError) as error:
    raise ToolExecutionError(
      {"error": type(error).__name__, "message": str(error)}
    ) from error
  return typing.cast(JSONValue, result.model_dump(mode="json"))


@AgentManager.tool(
  RECORD_SUPERSESSION_TOOL,
  description=(
    f"Record {SUPERSEDES_RELATION!r}: the successor is authorized to replace "
    "the predecessor across its entire scope on the same subject."
  ),
)
async def record_supersession(input: SupersessionProposal) -> JSONValue:
  return await _exact_result(
    SupersessionBehaviorResolver.record_supersession(
      input.successor_block_id,
      input.predecessor_block_id,
    )
  )


@AgentManager.tool(
  RECORD_REFINEMENT_TOOL,
  description=(
    f"Record {REFINES_RELATION!r}: new compatible detail at equal or narrower scope "
    "on the same subject, not mere extraction or rewording. The predecessor "
    "remains independently usable as a coarser description."
  ),
)
async def record_refinement(input: RefinementProposal) -> JSONValue:
  return await _exact_result(
    RefinementBehaviorResolver.record_refinement(
      input.refinement_block_id,
      input.predecessor_block_id,
    )
  )


@AgentManager.tool(
  RECORD_EVIDENCE_STANCE_TOOL,
  description=(
    "Record attributable evidence supporting or challenging a whole "
    "assertion in comparable scope, without declaring it true or false."
  ),
)
async def record_evidence_stance(input: EvidenceStanceProposal) -> JSONValue:
  return await _exact_result(
    EvidenceStanceBehaviorResolver.record_evidence_stance(
      input.evidence_block_id,
      input.assertion_block_id,
      input.stance,
    )
  )


@AgentManager.tool(
  CREATE_SYNTHESIS_TOOL,
  description=(
    "Create reusable multi-source information preserving provenance, "
    "disagreement, uncertainty and speaker attribution; copies do not "
    "multiply corroboration."
  ),
)
async def create_synthesis(input: SynthesisProposal) -> JSONValue:
  return await _exact_result(
    SynthesisBehaviorResolver.create_synthesis(
      input.text,
      input.source_block_ids,
      input.previous_synthesis_block_id,
    )
  )


@AgentManager.tool(
  ANCHOR_EXISTING_REFERENT_TOOL,
  description=(
    "Link a source's referring fragment to an existing identity-bearing "
    "referent, without creating a new referent."
  ),
)
async def anchor_existing_referent(
  input: ExistingReferentAnchorProposal,
) -> JSONValue:
  return await _exact_result(
    ExistingReferentAnchoringBehaviorResolver.anchor_existing_referent(
      input.source_block_id,
      input.selected_text,
      input.referent_block_id,
    )
  )


@AgentManager.tool(
  RECORD_DUPLICATE_ASSERTION_TOOL,
  description=(
    f"Record {DUPLICATES_ASSERTION_RELATION!r}: whole assertions from the same "
    "provenance occurrence with no "
    "independent evidence, reasoning, decision or material gain; matching "
    "words alone are insufficient."
  ),
)
async def record_duplicate_assertion(input: DuplicateAssertionProposal) -> JSONValue:
  return await _exact_result(
    DuplicateAssertionBehaviorResolver.record_duplicate_assertion(
      input.left_block_id,
      input.right_block_id,
    )
  )


@AgentManager.tool(
  RECORD_ORGANIZATION_CANDIDATE_TOOL,
  description="Mark an organization candidate without executing the behavior.",
  input_model_factory=_candidate_input_model,
)
async def record_organization_candidate(
  input: RecordOrganizationCandidateInput,
) -> JSONValue:
  behavior = get_behavior_resolver(input.behavior)
  if behavior is None:
    raise ToolExecutionError({"error": "behavior_unavailable"})
  return await _exact_result(
    typing.cast(typing.Any, behavior).record_candidate(input.block_id)
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
