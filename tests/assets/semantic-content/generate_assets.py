"""Generate the repository-owned semantic-content acceptance assets."""

from __future__ import annotations

import json
from pathlib import Path
import wave
import zipfile

import av
from PIL import Image
from pypdf import PdfWriter


ASSET_DIRECTORY = Path(__file__).parent


def _write_image() -> None:
  image = Image.new("RGB", (3, 2), color=(32, 96, 160))
  image.save(ASSET_DIRECTORY / "image.png", format="PNG")


def _write_audio() -> None:
  with wave.open(str(ASSET_DIRECTORY / "audio.wav"), "wb") as audio:
    audio.setnchannels(1)
    audio.setsampwidth(2)
    audio.setframerate(8_000)
    audio.writeframes(b"\x00\x00" * 800)


def _write_video() -> None:
  with av.open(str(ASSET_DIRECTORY / "video.mp4"), mode="w") as container:
    stream = container.add_stream("mpeg4", rate=1)
    stream.width = 16
    stream.height = 16
    stream.pix_fmt = "yuv420p"

    frame = av.VideoFrame(width=16, height=16, format="yuv420p")
    for plane in frame.planes:
      plane.update(bytes(plane.buffer_size))
    for packet in stream.encode(frame):
      container.mux(packet)
    for packet in stream.encode():
      container.mux(packet)


def _write_pdf() -> None:
  writer = PdfWriter()
  writer.add_blank_page(width=72, height=72)
  writer.add_metadata({"/Title": "InKCre semantic content"})
  with (ASSET_DIRECTORY / "document.pdf").open("wb") as output:
    writer.write(output)


def _write_epub() -> None:
  with zipfile.ZipFile(ASSET_DIRECTORY / "book.epub", "w") as epub:
    epub.writestr(
      "mimetype",
      "application/epub+zip",
      compress_type=zipfile.ZIP_STORED,
    )
    epub.writestr(
      "META-INF/container.xml",
      """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
    )
    epub.writestr(
      "OEBPS/package.opf",
      """<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" unique-identifier="book-id" xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">
      urn:uuid:00000000-0000-0000-0000-000000000001
    </dc:identifier>
    <dc:title>InKCre semantic content</dc:title>
    <dc:creator>InKCre</dc:creator>
    <dc:language>en</dc:language>
    <meta property="dcterms:modified">2026-01-01T00:00:00Z</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
  </manifest>
  <spine/>
</package>
""",
    )
    epub.writestr(
      "OEBPS/nav.xhtml",
      """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Navigation</title></head><body/></html>
""",
    )


def _write_zip() -> None:
  with zipfile.ZipFile(ASSET_DIRECTORY / "archive.zip", "w") as archive:
    archive.writestr("hello.txt", "InKCre semantic content\n")


def _write_textual_and_generic_files() -> None:
  (ASSET_DIRECTORY / "plain.txt").write_text(
    "InKCre semantic content\n",
    encoding="utf-8",
  )
  (ASSET_DIRECTORY / "document.html").write_text(
    "<!doctype html><html><head><title>InKCre</title></head>"
    "<body><main>Semantic content</main></body></html>\n",
    encoding="utf-8",
  )
  (ASSET_DIRECTORY / "unknown.bin").write_bytes(b"InKCre\x00semantic-content\n")


def _verify_case_table() -> None:
  cases = json.loads((ASSET_DIRECTORY / "cases.json").read_text(encoding="utf-8"))
  missing = [
    case["file"] for case in cases if not (ASSET_DIRECTORY / case["file"]).is_file()
  ]
  if missing:
    raise RuntimeError(f"semantic-content assets missing after generation: {missing}")


def main() -> None:
  _write_image()
  _write_audio()
  _write_video()
  _write_pdf()
  _write_epub()
  _write_zip()
  _write_textual_and_generic_files()
  _verify_case_table()


if __name__ == "__main__":
  main()
