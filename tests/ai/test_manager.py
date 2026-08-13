"""AIManager capability gates and output validation."""

import asyncio
from collections.abc import Sequence

import pydantic
import pytest

from app.business.ai import (
  AIDialectAdapter,
  AIExecutionRequirement,
  AIFeatureUnavailableError,
  AIManager,
  AIOutputContractError,
)
from app.business.ai.main import _ExecutionTarget
from app.schemas.ai import (
  AIModelModel,
  AIProviderModel,
  AssistantMessage,
  ChatCapability,
  EmbeddingCapability,
  FunctionTool,
  Message,
  TextContentPart,
  ToolChoice,
  UserMessage,
)
from app.schemas.info_base.main import Vector


class _Config(pydantic.BaseModel):
  pass


class _Adapter(AIDialectAdapter):
  supported_features = {"chat": frozenset({"tool_calling"})}
  supported_input_modalities = {
    "embedding": frozenset({"text"}),
    "chat": frozenset({"text"}),
  }

  def __init__(self, vectors: tuple[Vector, ...] = ((0.1, 0.2),)) -> None:
    self.vectors = vectors

  async def embed(self, config, native_model_id, inputs, dimensions):
    return self.vectors

  async def chat(
    self,
    config: pydantic.BaseModel,
    native_model_id: str,
    messages: Sequence[Message],
    tools: Sequence[FunctionTool],
    tool_choice: ToolChoice | None,
  ) -> AssistantMessage:
    return AssistantMessage(content="done")

  def supports_tool_choice(self, tool_choice: ToolChoice) -> bool:
    return tool_choice == "auto"


def _target(adapter: AIDialectAdapter, *, tool_calling: bool = True):
  capabilities = [
    EmbeddingCapability(input_modalities=["text"], output_modalities=["vector"]),
    ChatCapability(
      input_modalities=["text"],
      output_modalities=["text"],
      features=["tool_calling"] if tool_calling else [],
    ),
  ]
  return _ExecutionTarget(
    AIModelModel(
      id=2,
      provider=1,
      native_model_id="model",
      capabilities=capabilities,
    ),
    AIProviderModel(
      id=1,
      name="provider",
      dialect="tests.ai.v1",
      config={},
    ),
    adapter,
    _Config(),
  )


def test_embed_rejects_wrong_count_and_dimensions(monkeypatch):
  monkeypatch.setattr(
    AIManager,
    "_load_target",
    classmethod(lambda _cls, _model: _target(_Adapter(vectors=()))),
  )
  with pytest.raises(AIOutputContractError, match="result count"):
    asyncio.run(AIManager.embed(2, ("text",), 2))

  monkeypatch.setattr(
    AIManager,
    "_load_target",
    classmethod(lambda _cls, _model: _target(_Adapter(vectors=((0.1,),)))),
  )
  with pytest.raises(AIOutputContractError, match="dimension"):
    asyncio.run(AIManager.embed(2, ("text",), 2))

  monkeypatch.setattr(
    AIManager,
    "_load_target",
    classmethod(lambda _cls, _model: _target(_Adapter(vectors=((0.0, 0.0),)))),
  )
  with pytest.raises(AIOutputContractError, match="non-zero"):
    asyncio.run(AIManager.embed(2, ("text",), 2))


def test_chat_requires_joint_tool_calling_support(monkeypatch):
  monkeypatch.setattr(
    AIManager,
    "_load_target",
    classmethod(lambda _cls, _model: _target(_Adapter(), tool_calling=False)),
  )

  with pytest.raises(AIFeatureUnavailableError, match="jointly support"):
    asyncio.run(
      AIManager.chat(
        2,
        (UserMessage(content=(TextContentPart(text="go"),)),),
        tools=(
          FunctionTool(id="tool", description="tool", input_schema={"type": "object"}),
        ),
      )
    )


def test_can_execute_requires_joint_model_and_dialect_support(monkeypatch):
  monkeypatch.setattr(
    AIManager,
    "_load_target",
    classmethod(lambda _cls, _model: _target(_Adapter())),
  )

  assert AIManager.can_execute(
    2,
    AIExecutionRequirement(
      capability="chat",
      input_modalities=frozenset({"text"}),
      output_modalities=frozenset({"text"}),
      features=frozenset({"tool_calling"}),
      tool_choice="auto",
    ),
  )
  assert not AIManager.can_execute(
    2,
    AIExecutionRequirement(
      capability="chat",
      input_modalities=frozenset({"text", "image"}),
      output_modalities=frozenset({"text"}),
    ),
  )
  assert not AIManager.can_execute(
    2,
    AIExecutionRequirement(
      capability="chat",
      input_modalities=frozenset({"text"}),
      output_modalities=frozenset({"text"}),
      tool_choice="required",
    ),
  )
