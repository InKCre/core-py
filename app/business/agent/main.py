"""Persisted Agent definition loading and exact Tool registry binding."""

from __future__ import annotations

from dataclasses import dataclass
import inspect
import typing

import pydantic

from app.business.ai import AIExecutionRequirement, AIManager
from app.engine import SessionLocal
from app.schemas import AgentDefinitionModel
from app.schemas.agent import AgentID
from app.schemas.ai import FunctionTool, SystemMessage, UserMessage

from .contracts import (
  AgentNotFoundError,
  AgentToolBindingError,
  AgentToolHandler,
  AgentToolInputModelFactory,
  BoundAgentTool,
  DuplicateAgentToolRegistrationError,
  MissingAgentToolError,
)
from .persistence import (
  InMemoryThreadPersistenceBackend,
  ThreadPersistenceBackend,
  ThreadState,
)
from .thread import Thread


HandlerT = typing.TypeVar("HandlerT", bound=typing.Callable[..., typing.Any])


@dataclass(frozen=True)
class _ToolRegistration:
  handler: AgentToolHandler
  original_handler: typing.Callable[..., typing.Any]
  description: str
  input_model: type[pydantic.BaseModel]
  input_model_factory: AgentToolInputModelFactory | None

  def bind(self, tool_id: str) -> BoundAgentTool:
    input_model = (
      self.input_model_factory()
      if self.input_model_factory is not None
      else self.input_model
    )
    if not isinstance(input_model, type) or not issubclass(input_model, pydantic.BaseModel):
      raise AgentToolBindingError(
        f"Agent Tool {tool_id!r} did not produce a Pydantic input model"
      )
    return BoundAgentTool(
      definition=FunctionTool(
        id=tool_id,
        description=self.description,
        input_schema=input_model.model_json_schema(),
      ),
      input_model=input_model,
      handler=self.handler,
    )


class AgentManager:
  """Agent-definition execution and peer-local exact Tool registry."""

  _TOOLS: dict[str, _ToolRegistration] = {}
  _persistence: ThreadPersistenceBackend = InMemoryThreadPersistenceBackend()

  @classmethod
  def can_execute(cls, agent_id: AgentID, input_modality: str) -> bool:
    """Return static local eligibility for one Agent and canonical input modality."""
    with SessionLocal() as db:
      definition = db.get(AgentDefinitionModel, agent_id)
    if definition is None:
      return False
    try:
      cls._bind_tools(definition.tools)
    except MissingAgentToolError:
      return False
    requires_tools = bool(definition.tools) or definition.tool_choice is not None
    return AIManager.can_execute(
      definition.model,
      AIExecutionRequirement(
        capability="chat",
        input_modalities=frozenset({"text", input_modality}),
        output_modalities=frozenset({"text"}),
        features=frozenset({"tool_calling"}) if requires_tools else frozenset(),
        tool_choice=definition.tool_choice,
      ),
    )

  @classmethod
  def tool(
    cls,
    tool_id: str,
    *,
    description: str,
    input_model_factory: AgentToolInputModelFactory | None = None,
  ) -> typing.Callable[[HandlerT], HandlerT]:
    """Register one function as a typed Agent Tool and return it unchanged."""
    if not tool_id:
      raise AgentToolBindingError("Agent Tool ID must not be empty")

    def decorator(handler: HandlerT) -> HandlerT:
      signature = inspect.signature(handler)
      parameters = tuple(signature.parameters.values())
      if len(parameters) != 1:
        raise AgentToolBindingError(
          f"Agent Tool {tool_id!r} handler must accept exactly one input model"
        )
      hints = typing.get_type_hints(handler)
      annotation = hints.get(parameters[0].name)
      if not isinstance(annotation, type) or not issubclass(annotation, pydantic.BaseModel):
        raise AgentToolBindingError(
          f"Agent Tool {tool_id!r} input must be annotated with a Pydantic model"
        )

      existing = cls._TOOLS.get(tool_id)
      if existing is not None:
        if (
          existing.original_handler is handler
          and existing.description == description
          and existing.input_model_factory is input_model_factory
        ):
          return handler
        raise DuplicateAgentToolRegistrationError(
          f"Agent Tool {tool_id!r} is already registered"
        )

      cls._TOOLS[tool_id] = _ToolRegistration(
        handler=typing.cast(AgentToolHandler, handler),
        original_handler=handler,
        description=description,
        input_model=annotation,
        input_model_factory=input_model_factory,
      )
      return handler

    return decorator

  @classmethod
  async def run(cls, agent_id: AgentID, initial_message: UserMessage) -> Thread:
    """Create one active Thread from a persisted Agent definition snapshot."""
    with SessionLocal() as db:
      definition = db.get(AgentDefinitionModel, agent_id)
    if definition is None:
      raise AgentNotFoundError(f"Agent {agent_id} does not exist")

    bound_tools = cls._bind_tools(definition.tools)
    state = ThreadState(
      model=definition.model,
      tools=tuple(tool.definition for tool in bound_tools),
      tool_choice=definition.tool_choice,
      max_model_calls_per_turn=definition.max_model_calls_per_turn,
      messages=(SystemMessage(content=definition.system_prompt),),
    )
    thread_id, persisted = await cls._persistence.create(state)
    thread = Thread(thread_id, persisted, cls._persistence, bound_tools)
    thread.start_turn(initial_message)
    return thread

  @classmethod
  def _bind_tools(cls, tool_ids: tuple[str, ...]) -> tuple[BoundAgentTool, ...]:
    bound: list[BoundAgentTool] = []
    for tool_id in tool_ids:
      registration = cls._TOOLS.get(tool_id)
      if registration is None:
        raise MissingAgentToolError(
          f"Agent definition references unavailable Tool {tool_id!r}"
        )
      bound.append(registration.bind(tool_id))
    return tuple(bound)
