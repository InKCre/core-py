"""OpenAI-compatible wire translation through the real installed SDK."""

import asyncio
import json

import httpx
from openai import AsyncOpenAI

from app.business.ai import OpenAICompatibleConfig, OpenAICompatibleDialect
from app.schemas.ai import (
  AssistantMessage,
  FunctionTool,
  NamedToolChoice,
  ToolCall,
  ToolResult,
  ToolResultMessage,
  UserMessage,
)


def _factory(handler):
  def create(config: OpenAICompatibleConfig) -> AsyncOpenAI:
    return AsyncOpenAI(
      api_key=config.api_key,
      base_url=config.base_url,
      http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

  return create


def test_embedding_preserves_provider_indices_and_request_contract():
  requests: list[dict] = []

  def handler(request: httpx.Request) -> httpx.Response:
    requests.append(json.loads(request.content))
    return httpx.Response(
      200,
      json={
        "object": "list",
        "model": "embed-model",
        "data": [
          {"object": "embedding", "index": 1, "embedding": [0.3, 0.4]},
          {"object": "embedding", "index": 0, "embedding": [0.1, 0.2]},
        ],
        "usage": {"prompt_tokens": 2, "total_tokens": 2},
      },
    )

  dialect = OpenAICompatibleDialect(_factory(handler))
  vectors = asyncio.run(
    dialect.embed(
      OpenAICompatibleConfig(
        api_key="test-key",
        base_url="https://provider.example/v1",
      ),
      "embed-model",
      ("first", "second"),
      2,
    )
  )

  assert vectors == ((0.1, 0.2), (0.3, 0.4))
  assert requests == [
    {
      "dimensions": 2,
      "encoding_format": "float",
      "input": ["first", "second"],
      "model": "embed-model",
    }
  ]


def test_chat_maps_canonical_tool_batches_and_nullable_choice():
  requests: list[dict] = []

  def handler(request: httpx.Request) -> httpx.Response:
    requests.append(json.loads(request.content))
    return httpx.Response(
      200,
      json={
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 1,
        "model": "chat-model",
        "choices": [
          {
            "index": 0,
            "finish_reason": "tool_calls",
            "message": {
              "role": "assistant",
              "content": None,
              "tool_calls": [
                {
                  "id": "call-next",
                  "type": "function",
                  "function": {
                    "name": "submit_graph",
                    "arguments": '{"blocks":[]}',
                  },
                }
              ],
            },
          }
        ],
        "usage": {
          "prompt_tokens": 1,
          "completion_tokens": 1,
          "total_tokens": 2,
        },
      },
    )

  dialect = OpenAICompatibleDialect(_factory(handler))
  preceding = AssistantMessage(
    tool_calls=(ToolCall(id="call-before", tool="draft_graph", arguments={}),)
  )
  result = asyncio.run(
    dialect.chat(
      OpenAICompatibleConfig(
        api_key="test-key",
        base_url="https://provider.example/v1",
      ),
      "chat-model",
      (
        UserMessage(content="ruminate"),
        preceding,
        ToolResultMessage(
          results=(
            ToolResult(
              tool_call_id="call-before",
              content={"blocks": []},
              is_error=False,
            ),
          )
        ),
      ),
      (
        FunctionTool(
          id="submit_graph",
          description="Persist a graph.",
          input_schema={"type": "object"},
        ),
      ),
      NamedToolChoice(tool="submit_graph"),
    )
  )

  assert result == AssistantMessage(
    tool_calls=(
      ToolCall(
        id="call-next",
        tool="submit_graph",
        arguments={"blocks": []},
      ),
    )
  )
  request = requests[0]
  assert request["tool_choice"] == {
    "type": "function",
    "function": {"name": "submit_graph"},
  }
  assert request["tools"][0]["function"]["parameters"] == {"type": "object"}
  assert request["messages"][-1] == {
    "role": "tool",
    "tool_call_id": "call-before",
    "content": '{"content":{"blocks":[]},"is_error":false}',
  }
