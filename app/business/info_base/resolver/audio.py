"""Exact audio resolver using metadata-only PyAV inspection."""

import asyncio
from dataclasses import dataclass
from io import BytesIO

import av
from av.stream import Disposition

from .contracts import ResolverContentError, UnsupportedResolverCapability
from .inspection import ByteContentFacts, detect_media_type, require_bytes
from .main import Resolver


@dataclass(frozen=True, slots=True)
class AudioSolvedContent(ByteContentFacts):
  container: str | None
  codec: str | None
  duration_ms: int | None
  channels: int | None
  sample_rate_hz: int | None
  bitrate_bps: int | None


def _container_name(format_name: str | None) -> str | None:
  if not format_name:
    return None
  names = format_name.split(",")
  return "mp4" if "mp4" in names else names[0]


def _duration_ms(container, stream) -> int | None:
  if stream.duration is not None and stream.time_base is not None:
    return round(float(stream.duration * stream.time_base) * 1000)
  if container.duration is not None:
    return round(container.duration / 1000)
  return None


def _primary_stream(streams):
  default = [stream for stream in streams if bool(stream.disposition & Disposition.default)]
  ordinary = [
    stream for stream in streams if not bool(stream.disposition & Disposition.attached_pic)
  ]
  candidates = default or ordinary or list(streams)
  return candidates[0] if candidates else None


def _inspect_audio(content: bytes) -> AudioSolvedContent:
  try:
    with av.open(BytesIO(content), mode="r") as container:
      stream = _primary_stream(container.streams.audio)
      if stream is None:
        raise ResolverContentError("core.audio.v1", "no audio stream")
      codec = stream.codec_context
      facts = AudioSolvedContent(
        content=content,
        byte_size=len(content),
        detected_media_type=detect_media_type(content),
        container=_container_name(container.format.name),
        codec=codec.name,
        duration_ms=_duration_ms(container, stream),
        channels=codec.channels,
        sample_rate_hz=codec.sample_rate,
        bitrate_bps=stream.bit_rate or container.bit_rate,
      )
  except ResolverContentError:
    raise
  except (av.FFmpegError, OSError, ValueError) as error:
    raise ResolverContentError("core.audio.v1", "invalid audio") from error
  return facts


class AudioResolver(
  Resolver[AudioSolvedContent, bytes],
  rso_type="core.audio.v1",
):
  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> AudioSolvedContent:
    del materialize_missing
    content = require_bytes(
      await self.get_raw_content(refresh=refresh),
      self.__rsotype__,
    )
    return await asyncio.to_thread(_inspect_audio, content)

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
