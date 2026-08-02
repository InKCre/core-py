"""Exact generic-file resolver for bytes without stronger semantics."""

import asyncio
from dataclasses import dataclass

from .contracts import UnsupportedResolverCapability
from .inspection import ByteContentFacts, detect_media_type, require_bytes
from .main import Resolver


@dataclass(frozen=True, slots=True)
class FileSolvedContent(ByteContentFacts):
  pass


def _inspect_file(content: bytes) -> FileSolvedContent:
  return FileSolvedContent(
    content=content,
    byte_size=len(content),
    detected_media_type=detect_media_type(content),
  )


class FileResolver(
  Resolver[FileSolvedContent, bytes],
  rso_type="core.file.v1",
):
  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> FileSolvedContent:
    del materialize_missing
    content = require_bytes(
      await self.get_raw_content(refresh=refresh),
      self.__rsotype__,
    )
    return await asyncio.to_thread(_inspect_file, content)

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
