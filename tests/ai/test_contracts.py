"""Canonical AI capability and message contract tests."""

import pydantic
import pytest

from app.schemas.ai import (
  AssistantMessage,
  ChatCapability,
  EmbeddingCapability,
  ToolCall,
  ToolResult,
  ToolResultMessage,
  TextContentPart,
  UserMessage,
  normalize_capabilities,
  validate_message_history,
)


def test_capabilities_are_typed_and_canonically_ordered():
  capabilities = normalize_capabilities(
    [
      EmbeddingCapability(input_modalities=["text"], output_modalities=["vector"]),
      ChatCapability(
        input_modalities=["text"],
        output_modalities=["text"],
        features=["tool_calling"],
      ),
    ]
  )

  assert [capability.type for capability in capabilities] == [
    "chat",
    "embedding",
  ]
  assert capabilities[0].features == ("tool_calling",)


def test_capability_set_fields_reject_duplicates():
  with pytest.raises(pydantic.ValidationError, match="duplicate values"):
    ChatCapability(
      input_modalities=["text", "text"],
      output_modalities=["text"],
    )

  with pytest.raises(ValueError, match="duplicate AI capability"):
    normalize_capabilities(
      [
        ChatCapability(input_modalities=["text"], output_modalities=["text"]),
        ChatCapability(input_modalities=["text"], output_modalities=["text"]),
      ]
    )


def test_message_history_requires_one_exact_adjacent_result_batch():
  assistant = AssistantMessage(
    tool_calls=(
      ToolCall(id="call-a", tool="first", arguments={}),
      ToolCall(id="call-b", tool="second", arguments={}),
    )
  )
  results = ToolResultMessage(
    results=(
      ToolResult(tool_call_id="call-b", content={"ok": True}),
      ToolResult(tool_call_id="call-a", content=None),
    )
  )

  user = UserMessage(content=(TextContentPart(text="go"),))
  history = validate_message_history((user, assistant, results))

  assert history == (user, assistant, results)


def test_message_history_rejects_unclosed_or_mismatched_tool_calls():
  assistant = AssistantMessage(
    tool_calls=(ToolCall(id="call-a", tool="first", arguments={}),)
  )

  with pytest.raises(ValueError, match="adjacent ToolResultMessage"):
    validate_message_history((assistant,))

  with pytest.raises(ValueError, match="exactly cover"):
    validate_message_history(
      (
        assistant,
        ToolResultMessage(results=(ToolResult(tool_call_id="call-b", content=None),)),
      )
    )
