"""Shared AI fact management and peer-local capability routing."""

from collections.abc import Sequence
from dataclasses import dataclass
import math
import typing

import pydantic
import sqlalchemy.dialects.postgresql

from app.database_contract.profile import BUILTIN_AI_DIALECTS_BY_ID
from app.engine import SessionLocal
from app.schemas.ai import (
  AICapabilityType,
  AIDialectID,
  AIDialectModel,
  AIModelCapability,
  AIModelID,
  AIModelModel,
  AIProviderModel,
  AssistantMessage,
  FunctionTool,
  Message,
  ToolChoice,
  validate_message_history,
)
from app.schemas.info_base.main import Vector

from .contracts import (
  AICapabilityUnavailableError,
  AIDialectAdapter,
  AIFeatureUnavailableError,
  AIModelDisabledError,
  AIModelNotFoundError,
  AIOutputContractError,
  AIProviderDisabledError,
  AIProviderNotFoundError,
  DuplicateAIDialectRegistrationError,
  InvalidAIProviderConfigError,
  UnknownAIDialectError,
)


ConfigModelT = typing.TypeVar("ConfigModelT", bound=pydantic.BaseModel)
AdapterT = typing.TypeVar("AdapterT", bound=type[AIDialectAdapter])


@dataclass(frozen=True)
class _DialectRegistration:
  adapter: AIDialectAdapter
  adapter_type: type[AIDialectAdapter]
  config_model: type[pydantic.BaseModel]
  description: str


@dataclass(frozen=True)
class _ExecutionTarget:
  model: AIModelModel
  provider: AIProviderModel
  adapter: AIDialectAdapter
  config: pydantic.BaseModel


class AIManager:
  """Sole domain manager for AI dialects, shared facts and execution."""

  _DIALECTS: dict[AIDialectID, _DialectRegistration] = {}

  @classmethod
  def register_dialect(
    cls,
    dialect_id: AIDialectID,
    *,
    description: str,
    config_model: type[ConfigModelT],
  ) -> typing.Callable[[AdapterT], AdapterT]:
    """Bind one adapter class to an exact ID and return it unchanged."""

    def decorator(adapter_type: AdapterT) -> AdapterT:
      existing = cls._DIALECTS.get(dialect_id)
      if existing is not None:
        if (
          existing.adapter_type is adapter_type
          and existing.config_model is config_model
          and existing.description == description
        ):
          return adapter_type
        raise DuplicateAIDialectRegistrationError(
          f"AI dialect {dialect_id!r} is already registered by "
          f"{existing.adapter_type.__qualname__}"
        )
      cls._DIALECTS[dialect_id] = _DialectRegistration(
        adapter=adapter_type(),
        adapter_type=adapter_type,
        config_model=config_model,
        description=description,
      )
      return adapter_type

    return decorator

  @classmethod
  def sync_dialects(cls) -> None:
    """Persist registered dialect catalog contracts during explicit bootstrap."""
    with SessionLocal() as db:
      for dialect_id, registration in cls._DIALECTS.items():
        builtin = BUILTIN_AI_DIALECTS_BY_ID.get(dialect_id)
        statement = sqlalchemy.dialects.postgresql.insert(AIDialectModel).values(
          id=dialect_id,
          description=(
            builtin.description if builtin is not None else registration.description
          ),
          config_schema=(
            builtin.config_schema
            if builtin is not None
            else registration.config_model.model_json_schema()
          ),
        )
        statement = statement.on_conflict_do_update(
          index_elements=[AIDialectModel.id],
          set_={
            "description": statement.excluded.description,
            "config_schema": statement.excluded.config_schema,
          },
        )
        db.exec(statement)  # type: ignore
      db.commit()

  @classmethod
  def _registration(cls, dialect_id: AIDialectID) -> _DialectRegistration:
    try:
      return cls._DIALECTS[dialect_id]
    except KeyError as error:
      raise UnknownAIDialectError(
        f"No local adapter implements AI dialect {dialect_id!r}"
      ) from error

  @classmethod
  def _load_target(cls, model_id: AIModelID) -> _ExecutionTarget:
    with SessionLocal() as db:
      model = db.get(AIModelModel, model_id)
      if model is None:
        raise AIModelNotFoundError(f"AI model {model_id} does not exist")
      if not model.enabled:
        raise AIModelDisabledError(f"AI model {model_id} is disabled")
      provider = db.get(AIProviderModel, model.provider)
      if provider is None:
        raise AIProviderNotFoundError(
          f"AI model {model_id} references missing provider {model.provider}"
        )
      if not provider.enabled:
        raise AIProviderDisabledError(f"AI provider {provider.id} is disabled")

    registration = cls._registration(provider.dialect)
    try:
      config = registration.config_model.model_validate(provider.config)
    except pydantic.ValidationError as error:
      raise InvalidAIProviderConfigError(
        f"AI provider {provider.id} does not satisfy dialect {provider.dialect!r}"
      ) from error
    return _ExecutionTarget(model, provider, registration.adapter, config)

  @staticmethod
  def _capability(
    model: AIModelModel,
    capability_type: AICapabilityType,
  ) -> AIModelCapability:
    capability = next(
      (item for item in model.capabilities if item.type == capability_type),
      None,
    )
    if capability is None:
      raise AICapabilityUnavailableError(
        f"AI model {model.id} does not declare {capability_type!r}"
      )
    return capability

  @staticmethod
  def _require_modalities(
    model: AIModelModel,
    capability: AIModelCapability,
    *,
    input_: str,
    output: str,
  ) -> None:
    if (
      input_ not in capability.input_modalities
      or output not in capability.output_modalities
    ):
      raise AICapabilityUnavailableError(
        f"AI model {model.id} {capability.type!r} does not support {input_!r} -> {output!r}"
      )

  @classmethod
  async def embed(
    cls,
    model: AIModelID,
    inputs: Sequence[str],
    dimensions: int,
  ) -> tuple[Vector, ...]:
    """Embed one ordered non-empty text batch through the selected model."""
    if not inputs:
      raise ValueError("embedding inputs must not be empty")
    if dimensions <= 0:
      raise ValueError("embedding dimensions must be positive")
    target = cls._load_target(model)
    capability = cls._capability(target.model, "embedding")
    cls._require_modalities(
      target.model,
      capability,
      input_="text",
      output="vector",
    )
    vectors = await target.adapter.embed(
      target.config,
      target.model.native_model_id,
      tuple(inputs),
      dimensions,
    )
    if len(vectors) != len(inputs):
      raise AIOutputContractError(
        f"Embedding result count {len(vectors)} does not match input count {len(inputs)}"
      )
    for vector in vectors:
      if len(vector) != dimensions:
        raise AIOutputContractError(
          f"Embedding dimension {len(vector)} does not match requested {dimensions}"
        )
      if not vector or not all(math.isfinite(value) for value in vector):
        raise AIOutputContractError("Embedding vectors must be finite and non-empty")
      if not any(value != 0 for value in vector):
        raise AIOutputContractError("Embedding vectors must be non-zero")
    return vectors

  @classmethod
  async def chat(
    cls,
    model: AIModelID,
    messages: Sequence[Message],
    tools: Sequence[FunctionTool] = (),
    tool_choice: ToolChoice | None = None,
  ) -> AssistantMessage:
    """Execute one provider-neutral chat model call without owning history."""
    history = validate_message_history(messages)
    target = cls._load_target(model)
    capability = cls._capability(target.model, "chat")
    cls._require_modalities(
      target.model,
      capability,
      input_="text",
      output="text",
    )

    tool_ids = tuple(tool.id for tool in tools)
    if len(tool_ids) != len(set(tool_ids)):
      raise ValueError("Tool IDs must be unique")
    requires_tool_calling = bool(tools) or tool_choice is not None
    if requires_tool_calling:
      if "tool_calling" not in capability.features or not target.adapter.supports_feature(
        "chat", "tool_calling"
      ):
        raise AIFeatureUnavailableError(
          f"AI model {model} and dialect {target.provider.dialect!r} do not jointly "
          "support tool_calling"
        )
    if tool_choice is not None:
      if not tools:
        raise ValueError("tool_choice requires at least one Tool")
      if not target.adapter.supports_tool_choice(tool_choice):
        raise AIFeatureUnavailableError(
          f"AI dialect {target.provider.dialect!r} cannot represent tool_choice"
        )

    return await target.adapter.chat(
      target.config,
      target.model.native_model_id,
      history,
      tuple(tools),
      tool_choice,
    )
