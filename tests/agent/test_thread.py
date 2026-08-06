"""Deterministic Agent Thread, Turn, Tool and persistence lifecycle tests."""

import asyncio

import pydantic
import pytest

from app.business.agent import (
  AgentTurnActiveError,
  BoundAgentTool,
  InMemoryThreadPersistenceBackend,
  Thread,
  ThreadState,
  ToolExecutionError,
  TurnTermination,
)
from app.business.ai import AIManager
from app.schemas.ai import (
  AssistantMessage,
  FunctionTool,
  SystemMessage,
  ToolCall,
  ToolResultMessage,
  UserMessage,
)


class _ValueInput(pydantic.BaseModel):
  value: int


def _bound_tool(tool_id, handler):
  return BoundAgentTool(
    definition=FunctionTool(
      id=tool_id,
      description=tool_id,
      input_schema=_ValueInput.model_json_schema(),
    ),
    input_model=_ValueInput,
    handler=handler,
  )


async def _thread(*, tools=(), messages=None, max_model_calls=2):
  backend = InMemoryThreadPersistenceBackend()
  state = ThreadState(
    model=7,
    tools=tuple(tool.definition for tool in tools),
    tool_choice="auto" if tools else None,
    max_model_calls_per_turn=max_model_calls,
    messages=messages or (SystemMessage(content="system"),),
  )
  thread_id, persisted = await backend.create(state)
  return Thread(thread_id, persisted, backend, tools), backend


def test_natural_completion_persists_user_and_assistant(monkeypatch):
  async def scenario():
    async def chat(_cls, model, messages, tools, tool_choice):
      assert model == 7
      assert isinstance(messages[-1], UserMessage)
      assert tools == ()
      assert tool_choice is None
      return AssistantMessage(content="done")

    monkeypatch.setattr(AIManager, "chat", classmethod(chat))
    thread, _backend = await _thread()
    outcome = await thread.start_turn(UserMessage(content="begin"))

    assert outcome == TurnTermination.COMPLETED
    assert [message.type for message in thread.messages] == [
      "system",
      "user",
      "assistant",
    ]

  asyncio.run(scenario())


def test_tool_calls_execute_concurrently_and_commit_one_closed_pair(monkeypatch):
  async def scenario():
    started = 0
    both_started = asyncio.Event()

    async def handler(input: _ValueInput):
      nonlocal started
      started += 1
      if started == 2:
        both_started.set()
      await asyncio.wait_for(both_started.wait(), timeout=0.2)
      return {"value": input.value}

    tool = _bound_tool("parallel", handler)

    async def chat(_cls, model, messages, tools, tool_choice):
      return AssistantMessage(
        tool_calls=(
          ToolCall(id="first", tool="parallel", arguments={"value": 1}),
          ToolCall(id="second", tool="parallel", arguments={"value": 2}),
        )
      )

    monkeypatch.setattr(AIManager, "chat", classmethod(chat))
    thread, _backend = await _thread(tools=(tool,), max_model_calls=1)
    outcome = await thread.start_turn(UserMessage(content="begin"))

    assert outcome == TurnTermination.MAX_MODEL_CALLS
    assert [message.type for message in thread.messages] == [
      "system",
      "user",
      "assistant",
      "tool_result",
    ]
    results = thread.messages[-1]
    assert isinstance(results, ToolResultMessage)
    assert {result.tool_call_id for result in results.results} == {"first", "second"}
    assert not any(result.is_error for result in results.results)

  asyncio.run(scenario())


def test_completed_tool_batch_continues_to_the_next_model_call(monkeypatch):
  async def scenario():
    async def handler(input: _ValueInput):
      return {"value": input.value}

    tool = _bound_tool("probe", handler)
    model_calls = 0

    async def chat(_cls, model, messages, tools, tool_choice):
      nonlocal model_calls
      model_calls += 1
      if model_calls == 1:
        return AssistantMessage(
          tool_calls=(ToolCall(id="probe", tool="probe", arguments={"value": 1}),)
        )
      assert isinstance(messages[-1], ToolResultMessage)
      return AssistantMessage(content="done")

    monkeypatch.setattr(AIManager, "chat", classmethod(chat))
    thread, _backend = await _thread(tools=(tool,), max_model_calls=2)
    outcome = await thread.start_turn(UserMessage(content="begin"))

    assert outcome == TurnTermination.COMPLETED
    assert model_calls == 2
    assert [message.type for message in thread.messages] == [
      "system",
      "user",
      "assistant",
      "tool_result",
      "assistant",
    ]

  asyncio.run(scenario())


def test_tool_failures_are_isolated_and_reported_per_call(monkeypatch):
  async def scenario():
    async def owned_failure(input: _ValueInput):
      raise ToolExecutionError({"adjust": input.value})

    async def unexpected_failure(input: _ValueInput):
      raise RuntimeError(f"failed {input.value}")

    owned = _bound_tool("owned", owned_failure)
    unexpected = _bound_tool("unexpected", unexpected_failure)

    async def chat(_cls, model, messages, tools, tool_choice):
      return AssistantMessage(
        tool_calls=(
          ToolCall(id="invalid", tool="owned", arguments={"value": "wrong"}),
          ToolCall(id="owned", tool="owned", arguments={"value": 2}),
          ToolCall(id="unexpected", tool="unexpected", arguments={"value": 3}),
          ToolCall(id="unknown", tool="not-exposed", arguments={}),
        )
      )

    monkeypatch.setattr(AIManager, "chat", classmethod(chat))
    thread, _backend = await _thread(tools=(owned, unexpected), max_model_calls=1)
    await thread.start_turn(UserMessage(content="begin"))

    result_message = thread.messages[-1]
    assert isinstance(result_message, ToolResultMessage)
    results = {result.tool_call_id: result for result in result_message.results}
    assert all(result.is_error for result in results.values())
    assert isinstance(results["invalid"].content, list)
    assert results["owned"].content == {"adjust": 2}
    assert results["unexpected"].content == {"error": "tool_execution_failed"}
    assert results["unknown"].content == {
      "error": "unknown_tool",
      "tool": "not-exposed",
    }

  asyncio.run(scenario())


def test_turn_cancellation_cancels_tools_without_persisting_half_pair(monkeypatch):
  async def scenario():
    started = asyncio.Event()

    async def handler(input: _ValueInput):
      started.set()
      await asyncio.Event().wait()
      return {"value": input.value}

    tool = _bound_tool("wait", handler)

    async def chat(_cls, model, messages, tools, tool_choice):
      return AssistantMessage(
        tool_calls=(ToolCall(id="wait", tool="wait", arguments={"value": 1}),)
      )

    monkeypatch.setattr(AIManager, "chat", classmethod(chat))
    thread, _backend = await _thread(tools=(tool,))
    turn = thread.start_turn(UserMessage(content="begin"))
    await started.wait()
    turn.cancel()
    with pytest.raises(asyncio.CancelledError):
      await turn

    assert [message.type for message in thread.messages] == ["system", "user"]

  asyncio.run(scenario())


def test_new_turn_recovers_one_incomplete_trailing_tool_message(monkeypatch):
  async def scenario():
    incomplete = AssistantMessage(
      tool_calls=(ToolCall(id="lost", tool="old", arguments={}),)
    )
    thread, _backend = await _thread(messages=(SystemMessage(content="system"), incomplete))

    async def chat(_cls, model, messages, tools, tool_choice):
      assert [message.type for message in messages] == ["system", "user"]
      return AssistantMessage(content="recovered")

    monkeypatch.setattr(AIManager, "chat", classmethod(chat))
    outcome = await thread.start_turn(UserMessage(content="new input"))

    assert outcome == TurnTermination.COMPLETED
    assert [message.type for message in thread.messages] == [
      "system",
      "user",
      "assistant",
    ]

  asyncio.run(scenario())


def test_thread_rejects_a_second_active_turn(monkeypatch):
  async def scenario():
    release = asyncio.Event()

    async def chat(_cls, model, messages, tools, tool_choice):
      await release.wait()
      return AssistantMessage(content="done")

    monkeypatch.setattr(AIManager, "chat", classmethod(chat))
    thread, _backend = await _thread()
    first = thread.start_turn(UserMessage(content="first"))
    with pytest.raises(AgentTurnActiveError):
      thread.start_turn(UserMessage(content="second"))
    release.set()
    await first

  asyncio.run(scenario())
