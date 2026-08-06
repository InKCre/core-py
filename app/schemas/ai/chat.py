"""Canonical AI chat, Tool and ToolResult contracts."""

import typing

import pydantic


JSONValue: typing.TypeAlias = pydantic.JsonValue


class FunctionTool(pydantic.BaseModel):
  """One caller-owned function Tool exposed to an AI model."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  id: str = pydantic.Field(min_length=1)
  description: str
  input_schema: dict[str, JSONValue]


class ToolCall(pydantic.BaseModel):
  """One model-authored request to invoke a caller-owned Tool."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  id: str = pydantic.Field(min_length=1)
  tool: str = pydantic.Field(min_length=1)
  arguments: dict[str, JSONValue]


class ToolResult(pydantic.BaseModel):
  """One caller-side result correlated to a ToolCall."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  tool_call_id: str = pydantic.Field(min_length=1)
  content: JSONValue
  is_error: bool = False


class NamedToolChoice(pydantic.BaseModel):
  """Require one exact caller-owned Tool."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  type: typing.Literal["function"] = "function"
  tool: str = pydantic.Field(min_length=1)


ToolChoice: typing.TypeAlias = typing.Literal["none", "auto", "required"] | NamedToolChoice


class SystemMessage(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  type: typing.Literal["system"] = "system"
  content: str


class UserMessage(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  type: typing.Literal["user"] = "user"
  content: str


class AssistantMessage(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  type: typing.Literal["assistant"] = "assistant"
  content: str | None = None
  tool_calls: tuple[ToolCall, ...] = ()

  @pydantic.model_validator(mode="after")
  def unique_tool_call_ids(self) -> "AssistantMessage":
    call_ids = tuple(call.id for call in self.tool_calls)
    if len(call_ids) != len(set(call_ids)):
      raise ValueError("AssistantMessage ToolCall IDs must be unique")
    return self


class ToolResultMessage(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  type: typing.Literal["tool_result"] = "tool_result"
  results: tuple[ToolResult, ...] = pydantic.Field(min_length=1)

  @pydantic.model_validator(mode="after")
  def unique_tool_call_ids(self) -> "ToolResultMessage":
    call_ids = tuple(result.tool_call_id for result in self.results)
    if len(call_ids) != len(set(call_ids)):
      raise ValueError("ToolResultMessage ToolCall IDs must be unique")
    return self


Message: typing.TypeAlias = typing.Annotated[
  SystemMessage | UserMessage | AssistantMessage | ToolResultMessage,
  pydantic.Field(discriminator="type"),
]

_MESSAGES_ADAPTER = pydantic.TypeAdapter(tuple[Message, ...])


def validate_message_history(value: typing.Any) -> tuple[Message, ...]:
  """Validate canonical types and every closed Assistant/ToolResult pair."""
  messages = _MESSAGES_ADAPTER.validate_python(value)
  index = 0
  while index < len(messages):
    message = messages[index]
    if isinstance(message, ToolResultMessage):
      raise ValueError("ToolResultMessage must follow an AssistantMessage with ToolCalls")
    if isinstance(message, AssistantMessage) and message.tool_calls:
      if index + 1 >= len(messages) or not isinstance(
        messages[index + 1], ToolResultMessage
      ):
        raise ValueError("AssistantMessage ToolCalls require an adjacent ToolResultMessage")
      result_message = typing.cast(ToolResultMessage, messages[index + 1])
      call_ids = {call.id for call in message.tool_calls}
      result_ids = {result.tool_call_id for result in result_message.results}
      if result_ids != call_ids:
        raise ValueError("ToolResultMessage must exactly cover preceding ToolCall IDs")
      index += 2
      continue
    index += 1
  return messages
