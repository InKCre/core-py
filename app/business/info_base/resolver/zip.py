"""Exact ZIP resolver using central-directory metadata only."""

import asyncio
from dataclasses import dataclass
from io import BytesIO
import zipfile

from .contracts import ResolverContentError, UnsupportedResolverCapability
from .inspection import ByteContentFacts, require_bytes
from .main import Resolver


@dataclass(frozen=True, slots=True)
class ZIPSolvedContent(ByteContentFacts):
  member_count: int
  total_compressed_bytes: int
  total_uncompressed_bytes: int
  compression_methods: tuple[int, ...]
  encrypted_member_count: int


def _inspect_zip(content: bytes) -> ZIPSolvedContent:
  try:
    with zipfile.ZipFile(BytesIO(content)) as archive:
      members = archive.infolist()
  except (zipfile.BadZipFile, OSError, ValueError) as error:
    raise ResolverContentError("core.zip.v1", "invalid ZIP archive") from error

  return ZIPSolvedContent(
    content=content,
    byte_size=len(content),
    detected_media_type="application/zip",
    member_count=len(members),
    total_compressed_bytes=sum(member.compress_size for member in members),
    total_uncompressed_bytes=sum(member.file_size for member in members),
    compression_methods=tuple(sorted({member.compress_type for member in members})),
    encrypted_member_count=sum(bool(member.flag_bits & 0x1) for member in members),
  )


class ZIPResolver(
  Resolver[ZIPSolvedContent, bytes],
  rso_type="core.zip.v1",
):
  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> ZIPSolvedContent:
    del materialize_missing
    content = require_bytes(
      await self.get_raw_content(refresh=refresh),
      self.__rsotype__,
    )
    return await asyncio.to_thread(_inspect_zip, content)

  async def get_text(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> None:
    del refresh, materialize_missing
    raise UnsupportedResolverCapability(self.__rsotype__, "text")

  async def get_label(self, *, refresh: bool = False) -> str:
    del refresh
    return "ZIP"
