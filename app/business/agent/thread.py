"""Cancellable Agent Thread and per-turn model/Tool orchestration."""

from __future__ import annotations

import asyncio
from enum import StrEnum
import inspect
import json
import logging
import typing

import pydantic

from app.business.ai import AIManager
from app.schemas.ai import (
  AssistantMessage,
  JSONValue,
  ToolCall,
  ToolResult,
  ToolResultMessage,
  UserMessage,
)

from .contracts import AgentTurnActiveError, BoundAgentTool, ToolExecutionError
from .persistence import ThreadID, ThreadPersistenceBackend, ThreadState


logger = logging.getLogger(__name__)


class TurnTermination(StrEnum):
  COMPLETED = "completed"
  MAX_MODEL_CALLS = "max_model_calls"


class Thread:
  """One persisted Agent-definition snapshot with at most one active Turn."""

  def __init__(
    self,
    thread_id: ThreadID,
    state: ThreadState,
    persistence: ThreadPersistenceBackend,
    tools: tuple[BoundAgentTool, ...],
  ) -> None:
    self.id = thread_id
    self._state = state
    self._persistence = persistence
    self._tools = {tool.definition.id: tool for tool in tools}
    self.current_turn: asyncio.Task[TurnTermination] | None = None

  @property
  def messages(self):
    return self._state.messages

  @property
  def model(self):
    return self._state.model

  @property
  def tools(self):
    return self._state.tools

  @property
  def tool_choice(self):
    return self._state.tool_choice

  @property
  def max_model_calls_per_turn(self):
    return self._state.max_model_calls_per_turn

  async def refresh(self) -> ThreadState:
    """Refresh the local view from the persistence authority."""
    self._state = await self._persistence.read(self.id)
    return self._state

  def start_turn(self, input: UserMessage) -> asyncio.Task[TurnTermination]:
    """Schedule one complete model/Tool turn and return its cancellation handle."""
    if self.current_turn is not None and not self.current_turn.done():
      raise AgentTurnActiveError(f"Thread {self.id} already has an active Turn")
    self.current_turn = asyncio.create_task(
      self._run_turn(input),
      name=f"agent-thread-{self.id}",
    )
    return self.current_turn

  async def _run_turn(self, input: UserMessage) -> TurnTermination:
    self._state = await self._persistence.discard_trailing_incomplete_tool_calls(self.id)
    self._state = await self._persistence.append(self.id, (input,))
    model_calls = 0

    while True:
      model_calls += 1
      assistant = await AIManager.chat(
        self._state.model,
        self._state.messages,
        self._state.tools,
        self._state.tool_choice,
      )
      if not assistant.tool_calls:
        self._state = await self._persistence.append(self.id, (assistant,))
        return TurnTermination.COMPLETED

      results = await self._execute_tool_batch(assistant)
      self._state = await self._persistence.append(
        self.id,
        (assistant, ToolResultMessage(results=results)),
      )
      if model_calls >= self._state.max_model_calls_per_turn:
        return TurnTermination.MAX_MODEL_CALLS

  async def _execute_tool_batch(
    self,
    assistant: AssistantMessage,
  ) -> tuple[ToolResult, ...]:
    tasks = tuple(
      asyncio.create_task(
        self._execute_tool_call(call),
        name=f"agent-tool-{call.tool}-{call.id}",
      )
      for call in assistant.tool_calls
    )
    return tuple(await asyncio.gather(*tasks))

  async def _execute_tool_call(self, call: ToolCall) -> ToolResult:
    tool = self._tools.get(call.tool)
    if tool is None:
      return ToolResult(
        tool_call_id=call.id,
        content={"error": "unknown_tool", "tool": call.tool},
        is_error=True,
      )

    try:
      tool_input = tool.input_model.model_validate(call.arguments)
    except pydantic.ValidationError as error:
      return ToolResult(
        tool_call_id=call.id,
        content=typing.cast(JSONValue, json.loads(error.json())),
        is_error=True,
      )

    try:
      content = tool.handler(tool_input)
      if inspect.isawaitable(content):
        content = await content
      return ToolResult(tool_call_id=call.id, content=content)
    except ToolExecutionError as error:
      return ToolResult(
        tool_call_id=call.id,
        content=error.content,
        is_error=True,
      )
    except Exception:
      logger.exception("Unexpected Agent Tool failure", extra={"tool": call.tool})
      return ToolResult(
        tool_call_id=call.id,
        content={"error": "tool_execution_failed"},
        is_error=True,
      )
