"""OpenAI-compatible AI dialect across embedding and chat capabilities."""

from collections.abc import Callable, Sequence
import json
import typing

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
import pydantic

from app.schemas.ai import (
  AssistantMessage,
  FunctionTool,
  Message,
  NamedToolChoice,
  SystemMessage,
  ToolCall,
  ToolChoice,
  ToolResultMessage,
  UserMessage,
)
from app.schemas.info_base.main import Vector

from ..contracts import AIDialectAdapter, AIOutputContractError
from ..main import AIManager


class OpenAICompatibleConfig(pydantic.BaseModel):
  """Connection values for one OpenAI-compatible provider instance."""

  model_config = pydantic.ConfigDict(extra="forbid")

  api_key: str = pydantic.Field(min_length=1)
  base_url: str | None = pydantic.Field(default=None, min_length=1)


OpenAIClientFactory: typing.TypeAlias = Callable[[OpenAICompatibleConfig], AsyncOpenAI]


@AIManager.register_dialect(
  "core.openai-compatible.v1",
  description="OpenAI-compatible embedding and chat protocol.",
  config_model=OpenAICompatibleConfig,
)
class OpenAICompatibleDialect(AIDialectAdapter):
  """Translate canonical AI contracts through the OpenAI Python SDK."""

  supported_features = {"chat": frozenset({"tool_calling"})}

  def __init__(self, client_factory: OpenAIClientFactory | None = None) -> None:
    self._client_factory = client_factory or self._create_client

  @staticmethod
  def _create_client(config: OpenAICompatibleConfig) -> AsyncOpenAI:
    return AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)

  @staticmethod
  def _config(config: pydantic.BaseModel) -> OpenAICompatibleConfig:
    return OpenAICompatibleConfig.model_validate(config)

  async def embed(
    self,
    config: pydantic.BaseModel,
    native_model_id: str,
    inputs: Sequence[str],
    dimensions: int,
  ) -> tuple[Vector, ...]:
    client = self._client_factory(self._config(config))
    try:
      response = await client.embeddings.create(
        model=native_model_id,
        input=tuple(inputs),
        dimensions=dimensions,
        encoding_format="float",
      )
    finally:
      await client.close()

    by_index = {item.index: tuple(item.embedding) for item in response.data}
    expected = set(range(len(inputs)))
    if set(by_index) != expected:
      raise AIOutputContractError(
        "OpenAI-compatible embedding response indices do not cover the input batch"
      )
    return tuple(by_index[index] for index in range(len(inputs)))

  @staticmethod
  def _message_params(messages: Sequence[Message]) -> list[ChatCompletionMessageParam]:
    result: list[ChatCompletionMessageParam] = []
    for message in messages:
      if isinstance(message, SystemMessage):
        result.append({"role": "system", "content": message.content})
      elif isinstance(message, UserMessage):
        result.append({"role": "user", "content": message.content})
      elif isinstance(message, AssistantMessage):
        result.append(
          {
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
              {
                "id": call.id,
                "type": "function",
                "function": {
                  "name": call.tool,
                  "arguments": json.dumps(
                    call.arguments,
                    separators=(",", ":"),
                    sort_keys=True,
                  ),
                },
              }
              for call in message.tool_calls
            ],
          }
        )
      elif isinstance(message, ToolResultMessage):
        result.extend(
          {
            "role": "tool",
            "tool_call_id": tool_result.tool_call_id,
            "content": json.dumps(
              {
                "content": tool_result.content,
                "is_error": tool_result.is_error,
              },
              separators=(",", ":"),
              sort_keys=True,
            ),
          }
          for tool_result in message.results
        )
    return result

  @staticmethod
  def _tool_params(tools: Sequence[FunctionTool]) -> list[dict[str, typing.Any]]:
    return [
      {
        "type": "function",
        "function": {
          "name": tool.id,
          "description": tool.description,
          "parameters": tool.input_schema,
        },
      }
      for tool in tools
    ]

  @staticmethod
  def _tool_choice_param(tool_choice: ToolChoice) -> typing.Any:
    if isinstance(tool_choice, NamedToolChoice):
      return {
        "type": "function",
        "function": {"name": tool_choice.tool},
      }
    return tool_choice

  def supports_tool_choice(self, tool_choice: ToolChoice) -> bool:
    return isinstance(tool_choice, NamedToolChoice) or tool_choice in {
      "none",
      "auto",
      "required",
    }

  async def chat(
    self,
    config: pydantic.BaseModel,
    native_model_id: str,
    messages: Sequence[Message],
    tools: Sequence[FunctionTool],
    tool_choice: ToolChoice | None,
  ) -> AssistantMessage:
    client = self._client_factory(self._config(config))
    arguments: dict[str, typing.Any] = {
      "model": native_model_id,
      "messages": self._message_params(messages),
      "stream": False,
    }
    if tools:
      arguments["tools"] = self._tool_params(tools)
    if tool_choice is not None:
      arguments["tool_choice"] = self._tool_choice_param(tool_choice)

    try:
      response = typing.cast(
        ChatCompletion,
        await client.chat.completions.create(**arguments),
      )
    finally:
      await client.close()

    if not response.choices:
      raise AIOutputContractError("OpenAI-compatible chat response has no choices")
    message = response.choices[0].message
    calls: list[ToolCall] = []
    for call in message.tool_calls or ():
      if call.type != "function":
        raise AIOutputContractError(
          f"Unsupported OpenAI-compatible ToolCall type: {call.type!r}"
        )
      try:
        parsed_arguments = json.loads(call.function.arguments)
      except (TypeError, json.JSONDecodeError) as error:
        raise AIOutputContractError(
          f"ToolCall {call.id!r} arguments are not valid JSON"
        ) from error
      if not isinstance(parsed_arguments, dict):
        raise AIOutputContractError(f"ToolCall {call.id!r} arguments must be a JSON object")
      calls.append(
        ToolCall(
          id=call.id,
          tool=call.function.name,
          arguments=parsed_arguments,
        )
      )
    return AssistantMessage(content=message.content, tool_calls=tuple(calls))
