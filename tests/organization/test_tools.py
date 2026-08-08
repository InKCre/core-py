"""Resolver-owned draft schema and graph Tool contracts."""

import asyncio
import inspect
import typing

import pydantic
import pytest

from app.business.agent import AgentManager
from app.business.info_base.resolver import ResolverManager
from app.business.organization import (
  DRAFT_GRAPH_TOOL,
  GET_DRAFT_GRAPH_SCHEMA_TOOL,
  SUBMIT_GRAPH_TOOL,
)
from app.schemas.ai import JSONValue


def _tools():
  return {
    tool.definition.id: tool
    for tool in AgentManager._bind_tools(
      (
        GET_DRAFT_GRAPH_SCHEMA_TOOL,
        DRAFT_GRAPH_TOOL,
        SUBMIT_GRAPH_TOOL,
      )
    )
  }


def _exact_values(schema):
  if "const" in schema:
    return {schema["const"]}
  return set(schema["enum"])


async def _invoke(handler, input: pydantic.BaseModel) -> JSONValue:
  result = handler(input)
  if inspect.isawaitable(result):
    result = await result
  return typing.cast(JSONValue, result)


def test_bound_draft_tools_use_exact_resolver_enum_without_inline_native_schema():
  tools = _tools()
  available = {
    capability.resolver for capability in ResolverManager.get_draft_capabilities()
  }
  assert "core.text.v1" in available

  discovery_schema = typing.cast(
    dict[str, typing.Any], tools[GET_DRAFT_GRAPH_SCHEMA_TOOL].definition.input_schema
  )
  item_schema = discovery_schema["properties"]["resolvers"]["items"]
  assert _exact_values(item_schema) == available

  draft_schema = typing.cast(
    dict[str, typing.Any], tools[DRAFT_GRAPH_TOOL].definition.input_schema
  )
  assert _exact_values(draft_schema["properties"]["resolver"]) == available
  assert draft_schema["properties"]["input"]["type"] == "object"
  assert "text" not in str(draft_schema["properties"]["input"])


def test_schema_discovery_and_draft_share_resolver_owned_contract():
  async def scenario():
    tools = _tools()
    discovery = tools[GET_DRAFT_GRAPH_SCHEMA_TOOL]
    discovery_input = discovery.input_model.model_validate({"resolvers": ["core.text.v1"]})
    result = await _invoke(discovery.handler, discovery_input)
    assert isinstance(result, dict)
    resolver_schemas = result["resolvers"]
    assert isinstance(resolver_schemas, list)
    resolver_schema = resolver_schemas[0]
    assert isinstance(resolver_schema, dict)
    assert resolver_schema["resolver"] == "core.text.v1"
    input_schema = resolver_schema["input_schema"]
    assert isinstance(input_schema, dict)
    properties = input_schema["properties"]
    assert isinstance(properties, dict)
    assert properties["text"] == {
      "title": "Text",
      "type": "string",
    }

    draft = tools[DRAFT_GRAPH_TOOL]
    draft_input = draft.input_model.model_validate(
      {
        "resolver": "core.text.v1",
        "input": {"text": "A useful interpretation"},
        "id_start": -7,
      }
    )
    graph = await _invoke(draft.handler, draft_input)
    assert graph == {
      "blocks": [
        {
          "storage": None,
          "resolver": "core.text.v1",
          "content": "A useful interpretation",
          "id": -7,
        }
      ],
      "relations": [],
    }

    with pytest.raises(pydantic.ValidationError):
      draft.input_model.model_validate(
        {
          "resolver": "core.text.v1",
          "input": {"wrong": "shape"},
        }
      )

  asyncio.run(scenario())


def test_draft_resolver_enum_rejects_unavailable_source_native_resolver():
  draft = _tools()[DRAFT_GRAPH_TOOL]
  with pytest.raises(pydantic.ValidationError):
    draft.input_model.model_validate(
      {
        "resolver": "extensions.rss.feed_item.v1",
        "input": {},
      }
    )
