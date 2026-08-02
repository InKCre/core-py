"""Exact video resolver using metadata-only PyAV inspection."""

import asyncio
from dataclasses import dataclass
from fractions import Fraction
from io import BytesIO

import av

from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.main import SubGraphForm

from .audio import _container_name, _duration_ms, _primary_stream
from .contracts import ResolverContentError, UnsupportedResolverCapability
from .inspection import ByteContentFacts, detect_media_type, require_bytes
from .main import Resolver


@dataclass(frozen=True, slots=True)
class VideoSolvedContent(ByteContentFacts):
  container: str | None
  video_codec: str | None
  duration_ms: int | None
  width: int | None
  height: int | None
  frame_rate: float | None


def _frame_rate(rate: Fraction | None) -> float | None:
  return float(rate) if rate is not None else None


def _inspect_video(content: bytes) -> VideoSolvedContent:
  try:
    with av.open(BytesIO(content), mode="r") as container:
      stream = _primary_stream(container.streams.video)
      if stream is None:
        raise ResolverContentError("core.video.v1", "no video stream")
      codec = stream.codec_context
      facts = VideoSolvedContent(
        content=content,
        byte_size=len(content),
        detected_media_type=detect_media_type(content),
        container=_container_name(container.format.name),
        video_codec=codec.name,
        duration_ms=_duration_ms(container, stream),
        width=codec.width,
        height=codec.height,
        frame_rate=_frame_rate(stream.average_rate),
      )
  except ResolverContentError:
    raise
  except (av.FFmpegError, OSError, ValueError) as error:
    raise ResolverContentError("core.video.v1", "invalid video") from error
  return facts


class VideoResolver(
  Resolver[VideoSolvedContent, bytes],
  rso_type="core.video.v1",
):
  @classmethod
  def create_graph(cls, url: str) -> SubGraphForm:
    return SubGraphForm(block=BlockModel(resolver=cls.__rsotype__, content=url, storage=-1))

  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> VideoSolvedContent:
    del materialize_missing
    content = require_bytes(
      await self.get_raw_content(refresh=refresh),
      self.__rsotype__,
    )
    return await asyncio.to_thread(_inspect_video, content)

  async def get_text(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> None:
    del refresh, materialize_missing
    raise UnsupportedResolverCapability(self.__rsotype__, "text")

  async def get_str_for_embedding(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> None:
    del refresh, materialize_missing
    raise UnsupportedResolverCapability(self.__rsotype__, "embedding text")
