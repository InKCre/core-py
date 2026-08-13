"""Organization-facing completion, config, budget, and cancellation semantics."""

import asyncio

import pytest

from app.business.agent import AgentManager, AgentNotFoundError, TurnTermination
from app.business.deployment_config import DeploymentConfigManager
from app.business.organization import (
  OrganizationAgentNotFoundError,
  OrganizationExecutionError,
  OrganizationManager,
  OrganizationNotConfiguredError,
)
from app.schemas.ai import TextContentPart, UserMessage
from app.schemas.organization import RuminationConfig


class _Thread:
  def __init__(self, turn):
    self.current_turn = turn


def _user(text: str) -> UserMessage:
  return UserMessage(content=(TextContentPart(text=text),))


def _stub_context(monkeypatch, value: UserMessage | None):
  async def build(_cls, _block_id):
    return value

  monkeypatch.setattr(
    OrganizationManager,
    "_build_initial_message",
    classmethod(build),
  )


def test_cannot_understand_completes_without_config_or_agent(monkeypatch):
  async def scenario():
    _stub_context(monkeypatch, None)

    def unexpected_config(_cls, _key):
      raise AssertionError("config must not be read")

    async def unexpected_agent(_cls, _agent, _message):
      raise AssertionError("Agent must not start")

    monkeypatch.setattr(
      DeploymentConfigManager,
      "get",
      classmethod(unexpected_config),
    )
    monkeypatch.setattr(AgentManager, "run", classmethod(unexpected_agent))

    assert await OrganizationManager.ruminate_local(8) is None

  asyncio.run(scenario())


def test_missing_config_and_dangling_agent_are_distinct(monkeypatch):
  async def scenario():
    _stub_context(monkeypatch, _user("context"))
    monkeypatch.setattr(
      DeploymentConfigManager,
      "get",
      classmethod(lambda _cls, _key: None),
    )
    with pytest.raises(OrganizationNotConfiguredError):
      await OrganizationManager.ruminate_local(8)

    monkeypatch.setattr(
      DeploymentConfigManager,
      "get",
      classmethod(lambda _cls, _key: RuminationConfig(agent=-4)),
    )

    async def missing(_cls, _agent, _message):
      raise AgentNotFoundError("missing")

    monkeypatch.setattr(AgentManager, "run", classmethod(missing))
    with pytest.raises(OrganizationAgentNotFoundError):
      await OrganizationManager.ruminate_local(8)

  asyncio.run(scenario())


@pytest.mark.parametrize(
  ("outcome", "expected_error"),
  [
    (TurnTermination.COMPLETED, None),
    (TurnTermination.MAX_MODEL_CALLS, OrganizationExecutionError),
  ],
)
def test_turn_completion_is_shallow_and_budget_is_one_failure(
  monkeypatch,
  outcome,
  expected_error,
):
  async def scenario():
    _stub_context(monkeypatch, _user("context"))
    monkeypatch.setattr(
      DeploymentConfigManager,
      "get",
      classmethod(lambda _cls, _key: RuminationConfig(agent=3)),
    )
    turn = asyncio.create_task(asyncio.sleep(0, result=outcome))

    async def run(_cls, agent, message):
      assert agent == 3
      assert message == _user("context")
      return _Thread(turn)

    monkeypatch.setattr(AgentManager, "run", classmethod(run))
    if expected_error is None:
      assert await OrganizationManager.ruminate_local(8) is None
    else:
      with pytest.raises(expected_error):
        await OrganizationManager.ruminate_local(8)

  asyncio.run(scenario())


def test_caller_cancellation_propagates_to_active_turn(monkeypatch):
  async def scenario():
    _stub_context(monkeypatch, _user("context"))
    monkeypatch.setattr(
      DeploymentConfigManager,
      "get",
      classmethod(lambda _cls, _key: RuminationConfig(agent=3)),
    )
    started = asyncio.Event()

    async def wait_forever():
      started.set()
      await asyncio.Event().wait()

    turn = asyncio.create_task(wait_forever())

    async def run(_cls, _agent, _message):
      return _Thread(turn)

    monkeypatch.setattr(AgentManager, "run", classmethod(run))
    attempt = asyncio.create_task(OrganizationManager.ruminate_local(8))
    await started.wait()
    attempt.cancel()
    with pytest.raises(asyncio.CancelledError):
      await attempt
    assert turn.cancelled()

  asyncio.run(scenario())
