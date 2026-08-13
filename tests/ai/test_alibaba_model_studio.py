"""Alibaba Model Studio wire translation through the installed OpenAI SDK."""

import asyncio
import base64
import json

import httpx
from openai import AsyncOpenAI

from app.business.ai import AlibabaModelStudioDialect, OpenAICompatibleConfig
from app.schemas.ai import (
  AudioContentPart,
  ImageContentPart,
  TextContentPart,
  UserMessage,
  VideoContentPart,
)


def test_multimodal_parts_use_alibaba_extensions_and_stream_response():
  requests: list[dict] = []

  def handler(request: httpx.Request) -> httpx.Response:
    requests.append(json.loads(request.content))
    chunks = [
      {
        "id": "chatcmpl-1",
        "object": "chat.completion.chunk",
        "created": 1,
        "model": "qwen-omni",
        "choices": [
          {
            "index": 0,
            "delta": {"role": "assistant", "content": "scene"},
            "finish_reason": None,
          }
        ],
      },
      {
        "id": "chatcmpl-1",
        "object": "chat.completion.chunk",
        "created": 1,
        "model": "qwen-omni",
        "choices": [
          {
            "index": 0,
            "delta": {"content": " described"},
            "finish_reason": "stop",
          }
        ],
      },
    ]
    body = "".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks)
    body += "data: [DONE]\n\n"
    return httpx.Response(
      200,
      content=body,
      headers={"content-type": "text/event-stream"},
    )

  def factory(config: OpenAICompatibleConfig) -> AsyncOpenAI:
    return AsyncOpenAI(
      api_key=config.api_key.get_secret_value(),
      base_url=config.base_url,
      http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

  dialect = AlibabaModelStudioDialect(factory)
  result = asyncio.run(
    dialect.chat(
      OpenAICompatibleConfig(
        api_key="test-key",
        base_url="https://dashscope.example/compatible-mode/v1",
      ),
      "qwen-omni",
      (
        UserMessage(
          content=(
            TextContentPart(text="Describe these inputs."),
            ImageContentPart(data=b"image", mime_type="image/png"),
            AudioContentPart(data=b"audio", mime_type="audio/wav"),
            VideoContentPart(
              data=b"video",
              mime_type="video/mp4",
              transfer_url="https://media.example/video.mp4",
            ),
          )
        ),
      ),
      (),
      None,
    )
  )

  assert result.content == "scene described"
  request = requests[0]
  assert request["stream"] is True
  assert request["stream_options"] == {"include_usage": True}
  assert request["modalities"] == ["text"]
  parts = request["messages"][0]["content"]
  assert parts[0] == {"type": "text", "text": "Describe these inputs."}
  assert parts[1]["image_url"]["url"] == (
    "data:image/png;base64," + base64.b64encode(b"image").decode("ascii")
  )
  assert parts[2]["input_audio"] == {
    "data": "data:audio/wav;base64," + base64.b64encode(b"audio").decode("ascii"),
    "format": "wav",
  }
  assert parts[3]["video_url"]["url"].startswith("data:video/mp4;base64,")
