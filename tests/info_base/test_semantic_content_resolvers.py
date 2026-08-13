"""Black-box acceptance for exact core semantic-content resolvers."""

import asyncio
import datetime
from pathlib import Path

from app.business.info_base.resolver import (
  CORE_RESOLVER_IDS,
  ResolverContentError,
  ResolverManager,
  UnsupportedResolverCapability,
  register_core_resolvers,
)
from app.business.info_base.resolver.audio import AudioSolvedContent
from app.business.info_base.resolver.epub import EPUBSolvedContent
from app.business.info_base.resolver.file import FileSolvedContent
from app.business.info_base.resolver.image import ImageSolvedContent
from app.business.info_base.resolver.pdf import PDFSolvedContent
from app.business.info_base.resolver.video import VideoSolvedContent
from app.business.info_base.resolver.zip import ZIPSolvedContent
from app.business.info_base.storage import StorageManager
from app.schemas.info_base.block import BlockModel
import pytest


ASSETS = Path(__file__).parents[1] / "assets" / "semantic-content"


@pytest.fixture(scope="module", autouse=True)
def _generated_semantic_content_assets(semantic_content_assets: Path) -> None:
  assert semantic_content_assets == ASSETS


class _ByteStorage:
  def __init__(self, content: bytes):
    self.content = content

  async def get_raw_content(self, _pointer: str) -> bytes:
    return self.content


def _storage_backed_resolver(
  monkeypatch: pytest.MonkeyPatch,
  resolver_id: str,
  filename: str,
):
  content = (ASSETS / filename).read_bytes()
  storage = _ByteStorage(content)
  monkeypatch.setattr(
    StorageManager,
    "get_storage",
    classmethod(lambda _cls, _storage_id: storage),
  )
  block = BlockModel(
    id=31,
    resolver=resolver_id,
    content=f"asset:{filename}",
    storage=-4,
  )
  return ResolverManager.get(block), content


@pytest.mark.parametrize(
  ("resolver_id", "filename", "solved_type"),
  (
    ("core.image.v1", "image.png", ImageSolvedContent),
    ("core.audio.v1", "audio.wav", AudioSolvedContent),
    ("core.video.v1", "video.mp4", VideoSolvedContent),
    ("core.pdf.v1", "document.pdf", PDFSolvedContent),
    ("core.epub.v1", "book.epub", EPUBSolvedContent),
    ("core.zip.v1", "archive.zip", ZIPSolvedContent),
    ("core.file.v1", "unknown.bin", FileSolvedContent),
  ),
)
def test_real_storage_backed_samples_expose_bytes_and_typed_facts(
  monkeypatch,
  resolver_id,
  filename,
  solved_type,
):
  resolver, content = _storage_backed_resolver(monkeypatch, resolver_id, filename)

  solved = asyncio.run(resolver.get_solved_content())

  assert isinstance(solved, solved_type)
  assert solved.content == content
  assert solved.byte_size == len(content)


def test_real_image_audio_video_and_pdf_facts(monkeypatch):
  image, _ = _storage_backed_resolver(monkeypatch, "core.image.v1", "image.png")
  image_solved = asyncio.run(image.get_solved_content())
  assert (
    image_solved.format,
    image_solved.width,
    image_solved.height,
    image_solved.frame_count,
  ) == ("png", 3, 2, 1)

  audio, _ = _storage_backed_resolver(monkeypatch, "core.audio.v1", "audio.wav")
  audio_solved = asyncio.run(audio.get_solved_content())
  assert (
    audio_solved.container,
    audio_solved.codec,
    audio_solved.duration_ms,
    audio_solved.channels,
    audio_solved.sample_rate_hz,
  ) == ("wav", "pcm_s16le", 100, 1, 8_000)

  video, _ = _storage_backed_resolver(monkeypatch, "core.video.v1", "video.mp4")
  video_solved = asyncio.run(video.get_solved_content())
  assert (
    video_solved.container,
    video_solved.video_codec,
    video_solved.duration_ms,
    video_solved.width,
    video_solved.height,
    video_solved.frame_rate,
  ) == ("mp4", "mpeg4", 1_000, 16, 16, 1.0)

  pdf, _ = _storage_backed_resolver(monkeypatch, "core.pdf.v1", "document.pdf")
  pdf_solved = asyncio.run(pdf.get_solved_content())
  assert (
    pdf_solved.pdf_version,
    pdf_solved.page_count,
    pdf_solved.is_encrypted,
    pdf_solved.title,
    pdf_solved.author,
  ) == ("1.3", 1, False, "InKCre semantic content", None)


def test_real_video_exposes_source_native_subtitle_text(monkeypatch):
  resolver, _ = _storage_backed_resolver(
    monkeypatch,
    "core.video.v1",
    "video-subtitled.mkv",
  )

  solved = asyncio.run(resolver.get_solved_content())

  assert solved.subtitles == ("Flight software integration rehearsal",)


def test_real_epub_zip_and_generic_file_facts(monkeypatch):
  epub, _ = _storage_backed_resolver(monkeypatch, "core.epub.v1", "book.epub")
  epub_solved = asyncio.run(epub.get_solved_content())
  assert epub_solved.epub_version == "3.0"
  assert epub_solved.title == "InKCre semantic content"
  assert epub_solved.creators == ("InKCre",)
  assert epub_solved.languages == ("en",)
  assert epub_solved.modified_at == datetime.datetime(
    2026,
    1,
    1,
    tzinfo=datetime.timezone.utc,
  )
  assert (epub_solved.manifest_count, epub_solved.spine_count) == (1, 0)
  assert epub_solved.has_navigation is True

  archive, _ = _storage_backed_resolver(monkeypatch, "core.zip.v1", "archive.zip")
  archive_solved = asyncio.run(archive.get_solved_content())
  assert archive_solved.detected_media_type == "application/zip"
  assert archive_solved.member_count == 1
  assert archive_solved.total_compressed_bytes == 24
  assert archive_solved.total_uncompressed_bytes == 24
  assert archive_solved.compression_methods == (0,)
  assert archive_solved.encrypted_member_count == 0

  generic, _ = _storage_backed_resolver(monkeypatch, "core.file.v1", "unknown.bin")
  generic_solved = asyncio.run(generic.get_solved_content())
  assert generic_solved.detected_media_type is None


@pytest.mark.parametrize(
  ("resolver_id", "inline", "filename", "expected"),
  (
    ("core.text.v1", "authored text", None, "authored text"),
    ("core.html.v1", "<p>authored HTML</p>", None, "<p>authored HTML</p>"),
    ("core.text.v1", None, "plain.txt", "InKCre semantic content\n"),
    (
      "core.html.v1",
      None,
      "document.html",
      "<!doctype html><html><head><title>InKCre</title></head>"
      "<body><main>Semantic content</main></body></html>\n",
    ),
  ),
)
def test_text_and_html_support_inline_and_storage_backed_content(
  monkeypatch,
  resolver_id,
  inline,
  filename,
  expected,
):
  if filename is None:
    resolver = ResolverManager.get(BlockModel(resolver=resolver_id, content=inline))
  else:
    resolver, _ = _storage_backed_resolver(monkeypatch, resolver_id, filename)

  assert asyncio.run(resolver.get_solved_content()) == expected


def test_core_labels_are_resolver_qualified_and_block_local(monkeypatch):
  text = ResolverManager.get(
    BlockModel(
      resolver="core.text.v1",
      content="  First   meaningful line  \nsecond line",
    )
  )
  html = ResolverManager.get(
    BlockModel(
      resolver="core.html.v1",
      content=(
        "<html><head><title>  Useful title </title></head><body><h1>Body</h1></body></html>"
      ),
    )
  )
  pdf, _ = _storage_backed_resolver(monkeypatch, "core.pdf.v1", "document.pdf")

  assert asyncio.run(text.get_label()) == "text <First meaningful line>"
  assert asyncio.run(html.get_label()) == "html <Useful title>"
  assert asyncio.run(pdf.get_label()) == "PDF <InKCre semantic content>"

  epub, _ = _storage_backed_resolver(monkeypatch, "core.epub.v1", "book.epub")
  assert asyncio.run(epub.get_label()) == "EPUB <InKCre semantic content>"


def test_text_label_bounds_long_identifiers():
  resolver = ResolverManager.get(BlockModel(resolver="core.text.v1", content="x" * 120))

  assert asyncio.run(resolver.get_label()) == f"text <{'x' * 96}…>"


@pytest.mark.parametrize(
  "resolver_id",
  (
    "core.image.v1",
    "core.audio.v1",
    "core.video.v1",
    "core.pdf.v1",
    "core.epub.v1",
    "core.zip.v1",
  ),
)
def test_claimed_formats_reject_malformed_storage_bytes(monkeypatch, resolver_id):
  storage = _ByteStorage(b"not the claimed format")
  monkeypatch.setattr(
    StorageManager,
    "get_storage",
    classmethod(lambda _cls, _storage_id: storage),
  )
  resolver = ResolverManager.get(
    BlockModel(resolver=resolver_id, content="malformed", storage=-4)
  )

  with pytest.raises(ResolverContentError):
    asyncio.run(resolver.get_solved_content())


@pytest.mark.parametrize(
  "resolver_id",
  tuple(resolver for resolver in CORE_RESOLVER_IDS[2:] if resolver != "core.pdf.v1"),
)
def test_byte_resolvers_explicitly_reject_text_projection(
  monkeypatch,
  resolver_id,
):
  resolver, _ = _storage_backed_resolver(monkeypatch, resolver_id, "unknown.bin")

  with pytest.raises(UnsupportedResolverCapability):
    asyncio.run(resolver.get_text())


def test_pdf_exposes_body_capability_and_block_local_lexical_metadata(monkeypatch):
  resolver, _ = _storage_backed_resolver(monkeypatch, "core.pdf.v1", "document.pdf")

  body = "Deterministic recovery requires an authoritative write-ahead log."
  assert asyncio.run(resolver.get_text()) == body
  lexical = asyncio.run(resolver.get_text(context="lexical", materialize_missing=False))
  assert lexical is not None
  assert "title: InKCre semantic content" in lexical
  assert "pages: 1" in lexical
  assert body in lexical


def test_explicit_bootstrap_registers_exactly_the_nine_core_ids(monkeypatch):
  monkeypatch.setattr(ResolverManager, "RESOLVER_CLS", {})

  register_core_resolvers()

  assert tuple(ResolverManager.RESOLVER_CLS) == CORE_RESOLVER_IDS
  assert not {"text", "html", "image", "video"} & ResolverManager.RESOLVER_CLS.keys()
