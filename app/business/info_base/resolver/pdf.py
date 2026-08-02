"""Exact PDF resolver using bounded structural inspection."""

import asyncio
from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .contracts import ResolverContentError, UnsupportedResolverCapability
from .inspection import ByteContentFacts, detect_media_type, require_bytes
from .main import Resolver


@dataclass(frozen=True, slots=True)
class PDFSolvedContent(ByteContentFacts):
  pdf_version: str | None
  page_count: int | None
  is_encrypted: bool
  title: str | None
  author: str | None


def _metadata_text(metadata: object, attribute: str) -> str | None:
  value = getattr(metadata, attribute, None)
  return value if isinstance(value, str) else None


def _inspect_pdf(content: bytes) -> PDFSolvedContent:
  try:
    reader = PdfReader(BytesIO(content), strict=True)
    encrypted = reader.is_encrypted
    metadata = None if encrypted else reader.metadata
    page_count = None if encrypted else len(reader.pages)
  except (PdfReadError, OSError, ValueError, TypeError) as error:
    raise ResolverContentError("core.pdf.v1", "invalid PDF") from error

  header = reader.pdf_header
  version = header.removeprefix("%PDF-") if header.startswith("%PDF-") else None
  return PDFSolvedContent(
    content=content,
    byte_size=len(content),
    detected_media_type=detect_media_type(content),
    pdf_version=version,
    page_count=page_count,
    is_encrypted=encrypted,
    title=_metadata_text(metadata, "title"),
    author=_metadata_text(metadata, "author"),
  )


class PDFResolver(
  Resolver[PDFSolvedContent, bytes],
  rso_type="core.pdf.v1",
):
  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> PDFSolvedContent:
    del materialize_missing
    content = require_bytes(
      await self.get_raw_content(refresh=refresh),
      self.__rsotype__,
    )
    return await asyncio.to_thread(_inspect_pdf, content)

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
