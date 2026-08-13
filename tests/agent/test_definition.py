"""Agent definition and exact Tool registry contracts."""

import typing

import pydantic
import pytest

from app.business.agent import (
  AgentManager,
  AgentToolBindingError,
  DuplicateAgentToolRegistrationError,
  MissingAgentToolError,
)
from app.schemas import AgentDefinitionModel
from app.schemas.agent import normalize_agent_tools


class _Input(pydantic.BaseModel):
  value: int


def test_agent_tools_have_canonical_set_semantics():
  assert normalize_agent_tools(["zeta", "alpha"]) == ("alpha", "zeta")
  with pytest.raises(ValueError, match="unique"):
    normalize_agent_tools(["same", "same"])
  with pytest.raises(ValueError, match="empty"):
    normalize_agent_tools([""])

  definition = AgentDefinitionModel.model_validate(
    {
      "name": "agent",
      "system_prompt": "prompt",
      "tools": ["zeta", "alpha"],
      "model": 1,
      "max_model_calls_per_turn": 2,
    }
  )
  assert definition.tools == ("alpha", "zeta")


def test_tool_decorator_projects_pydantic_schema_and_rejects_collisions():
  class IsolatedAgentManager(AgentManager):
    _TOOLS = {}

  @IsolatedAgentManager.tool("probe", description="Return the probe value")
  async def probe(input: _Input):
    return {"value": input.value}

  bound = IsolatedAgentManager._bind_tools(("probe",))
  assert bound[0].definition.id == "probe"
  schema = typing.cast(dict[str, typing.Any], bound[0].definition.input_schema)
  assert schema["properties"]["value"]["type"] == "integer"

  with pytest.raises(DuplicateAgentToolRegistrationError):

    @IsolatedAgentManager.tool("probe", description="collision")
    async def collision(input: _Input):
      return {"value": input.value}

  with pytest.raises(MissingAgentToolError, match="unavailable"):
    IsolatedAgentManager._bind_tools(("missing",))


def test_tool_decorator_requires_one_pydantic_input():
  class IsolatedAgentManager(AgentManager):
    _TOOLS = {}

  with pytest.raises(AgentToolBindingError, match="exactly one"):

    @IsolatedAgentManager.tool("bad-arity", description="bad")
    async def bad_arity():
      return None

  with pytest.raises(AgentToolBindingError, match="Pydantic"):

    @IsolatedAgentManager.tool("bad-input", description="bad")
    async def bad_input(value: int):
      return value


def test_dynamic_input_schema_is_frozen_when_tools_are_bound():
  class IsolatedAgentManager(AgentManager):
    _TOOLS = {}

  version = 1

  def input_model_factory():
    return pydantic.create_model(
      "DynamicInput",
      value=(int, pydantic.Field(description=f"version {version}")),
    )

  @IsolatedAgentManager.tool(
    "dynamic",
    description="dynamic schema",
    input_model_factory=input_model_factory,
  )
  async def dynamic(input: pydantic.BaseModel):
    return input.model_dump(mode="json")

  first = IsolatedAgentManager._bind_tools(("dynamic",))[0]
  version = 2
  second = IsolatedAgentManager._bind_tools(("dynamic",))[0]

  first_schema = typing.cast(dict[str, typing.Any], first.definition.input_schema)
  second_schema = typing.cast(dict[str, typing.Any], second.definition.input_schema)
  first_description = first_schema["properties"]["value"]["description"]
  second_description = second_schema["properties"]["value"]["description"]
  assert first_description == "version 1"
  assert second_description == "version 2"
