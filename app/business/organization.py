"""Explicit focal-Block rumination composed from Agent and graph capabilities."""

from __future__ import annotations

import json
import logging
import typing

import pydantic

from app.business.agent import AgentManager, AgentNotFoundError, TurnTermination
from app.business.deployment_config import DeploymentConfigManager
from app.business.info_base import BlockManager, InfoBaseManager, RelationManager
from app.business.info_base.resolver import (
  ResolverDraftCapability,
  ResolverManager,
  UnknownResolverError,
  UnsupportedResolverCapability,
)
from app.business.peer import PeerManager
from app.engine import SessionLocal
from app.schemas.ai import JSONValue, TextContentPart, UserMessage
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel
from app.schemas.organization import (
  DraftGraphInput,
  GetDraftGraphSchemaInput,
  MediaInterpretationReport,
  RuminationConfig,
  RuminationRequest,
  SubmitGraphInput,
)
from app.schemas.peer import PeerProtocolRequest, PeerProtocolResponse, PeerRef


logger = logging.getLogger(__name__)

RUMINATION_CONFIG_KEY = "core.organization.rumination"
RUMINATION_CONFIG_SCHEMA = "core.organization.rumination.config.v1"
RUMINATION_CAPABILITY = "core.organization.rumination.v1"

GET_DRAFT_GRAPH_SCHEMA_TOOL = "get_draft_graph_schema"
DRAFT_GRAPH_TOOL = "draft_graph"
SUBMIT_GRAPH_TOOL = "submit_graph"


class OrganizationError(RuntimeError):
  """Base failure at the organization capability boundary."""


class OrganizationBlockNotFoundError(OrganizationError):
  pass


class OrganizationNotConfiguredError(OrganizationError):
  pass


class OrganizationAgentNotFoundError(OrganizationError):
  pass


class OrganizationExecutionError(OrganizationError):
  pass


class OrganizationDelegationError(OrganizationError):
  pass


DeploymentConfigManager.register_schema(RUMINATION_CONFIG_SCHEMA, RuminationConfig)


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
  description=(
    "Return code-owned draft-input JSON Schemas for selected exact Resolver IDs."
  ),
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
  description=(
    "Draft one rooted GraphForm through an exact Resolver without persisting it."
  ),
  input_model_factory=_draft_graph_input_model,
)
async def draft_graph(input: DraftGraphInput) -> JSONValue:
  capability = ResolverManager.get_draft_capability(input.resolver)
  resolver_input = typing.cast(
    pydantic.BaseModel,
    getattr(input, "_resolver_input"),
  )
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


class OrganizationManager:
  """Own the explicit organization entry while keeping rumination a small approach."""

  @classmethod
  def can_interpret_media(cls) -> bool:
    from app.business.organization_media import can_handle_media_interpretation

    return can_handle_media_interpretation()

  @classmethod
  async def interpret_missing_media(cls) -> MediaInterpretationReport:
    from app.business.organization_media import interpret_missing_media

    return await interpret_missing_media()

  @classmethod
  async def ruminate(
    cls,
    block_id: int,
    *,
    route_to_peer: PeerRef | None = None,
  ) -> None:
    """Execute locally unless the caller explicitly selects another Peer."""
    request = RuminationRequest(block=block_id)
    if route_to_peer is None or route_to_peer == PeerManager.get_current_peer_ref():
      await cls.ruminate_local(request.block)
      return

    payload = PeerProtocolRequest(
      body=typing.cast(
        JSONValue,
        request.model_dump(mode="json"),
      )
    )
    result = await PeerManager.delegate(
      RUMINATION_CAPABILITY,
      typing.cast(JSONValue, payload.model_dump(mode="json", exclude_unset=True)),
      route_to_peer=route_to_peer,
    )
    try:
      response = PeerProtocolResponse.model_validate(result)
    except pydantic.ValidationError as error:
      raise OrganizationDelegationError(
        "Rumination Peer returned an invalid response"
      ) from error
    if response.status != 204 or "body" in response.model_fields_set:
      raise OrganizationDelegationError(f"Rumination Peer returned HTTP {response.status}")

  @classmethod
  async def ruminate_local(cls, block_id: int) -> None:
    """Complete one local best-effort rumination attempt for a focal Block."""
    initial_message = await cls._build_initial_message(block_id)
    if initial_message is None:
      return

    config = DeploymentConfigManager.get(RUMINATION_CONFIG_KEY)
    if config is None:
      raise OrganizationNotConfiguredError("Rumination Agent is not configured")
    if not isinstance(config, RuminationConfig):
      raise TypeError("Rumination config registry returned the wrong model")

    try:
      thread = await AgentManager.run(config.agent, initial_message)
    except AgentNotFoundError as error:
      raise OrganizationAgentNotFoundError(
        f"Configured rumination Agent {config.agent} does not exist"
      ) from error

    turn = thread.current_turn
    if turn is None:  # pragma: no cover - AgentManager.run invariant
      raise OrganizationExecutionError("Rumination Agent did not start a Turn")
    outcome = await turn
    if outcome == TurnTermination.MAX_MODEL_CALLS:
      raise OrganizationExecutionError(
        "Rumination exceeded its configured per-Turn model-call budget"
      )

  @classmethod
  async def _build_initial_message(cls, block_id: int) -> UserMessage | None:
    with SessionLocal() as db:
      block = BlockManager.get(block_id, db)
      if block is None:
        raise OrganizationBlockNotFoundError(f"Block {block_id} does not exist")
      relations = tuple(
        sorted(
          RelationManager.get(block_id, db_session=db),
          key=lambda relation: typing.cast(int, relation.id),
        )
      )
      neighbor_ids = {
        relation.to_ if relation.from_ == block_id else relation.from_
        for relation in relations
      }
      neighbors = {
        neighbor_id: neighbor
        for neighbor_id in neighbor_ids
        if (neighbor := db.get(BlockModel, neighbor_id)) is not None
      }

    try:
      focal_text = await ResolverManager.get(block).get_text()
    except (UnknownResolverError, UnsupportedResolverCapability):
      return None
    except Exception as error:
      raise OrganizationExecutionError(
        "Rumination could not understand focal Block"
      ) from error
    if focal_text is None or not focal_text.strip():
      return None

    relation_context: list[dict[str, typing.Any]] = []
    for relation in relations:
      neighbor_id, direction = cls._neighbor_and_direction(block_id, relation)
      neighbor = neighbors.get(neighbor_id)
      label: str | None = None
      if neighbor is not None:
        try:
          label = await ResolverManager.get(neighbor).get_label()
        except Exception:
          logger.debug(
            "Could not project rumination neighbor label",
            exc_info=True,
            extra={"block": neighbor_id},
          )
      relation_context.append(
        {
          "id": relation.id,
          "direction": direction,
          "property": relation.content,
          "other_block": {
            "id": neighbor_id,
            "resolver": neighbor.resolver if neighbor is not None else None,
            "label": label,
          },
        }
      )

    context = {
      "request": "ruminate",
      "focal_block": {
        "id": block_id,
        "resolver": block.resolver,
        "text": focal_text,
      },
      "direct_relations": relation_context,
      "available_draft_resolvers": [
        {
          "resolver": capability.resolver,
          "description": capability.description,
        }
        for capability in ResolverManager.get_draft_capabilities()
      ],
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

  @staticmethod
  def _neighbor_and_direction(
    block_id: int,
    relation: RelationModel,
  ) -> tuple[int, typing.Literal["incoming", "outgoing", "self"]]:
    if relation.from_ == block_id and relation.to_ == block_id:
      return block_id, "self"
    if relation.from_ == block_id:
      return relation.to_, "outgoing"
    return relation.from_, "incoming"
