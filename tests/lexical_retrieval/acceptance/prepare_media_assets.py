"""Prepare ignored, pinned real-media assets for live lexical acceptance."""

from __future__ import annotations

import hashlib
from pathlib import Path

import av
from av.audio.resampler import AudioResampler
import httpx


ASSET_DIRECTORY = Path(__file__).parent / ".assets"
VIDEO_URL = (
  "https://images-assets.nasa.gov/video/"
  "GSFC_20140121_GPM_m11457_Dave_McComas/"
  "GSFC_20140121_GPM_m11457_Dave_McComas~mobile.mp4"
)
SUBTITLE_URL = (
  "https://images-assets.nasa.gov/video/"
  "GSFC_20140121_GPM_m11457_Dave_McComas/"
  "GSFC_20140121_GPM_m11457_Dave_McComas.vtt"
)
VIDEO_ETAG = '"926385c5b8fda0cfcc5b2da4b9d880da"'
SUBTITLE_ETAG = '"a3efda2ebbb163964c886152bdf20a5c"'
VIDEO_SHA256 = "03168dd86fe492fed362cb64d5ce3d29989b8573cd9dfdaebfed0e11512f7427"
SUBTITLE_SHA256 = "69d12ca3151641496096e074b81749ad4f3fb173fcc08b56ce012dd1eddcc40d"


def _digest(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as source:
    for chunk in iter(lambda: source.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def _download(url: str, path: Path, *, sha256: str, etag: str) -> None:
  if path.is_file() and _digest(path) == sha256:
    return
  temporary = path.with_suffix(path.suffix + ".part")
  with httpx.stream(
    "GET",
    url,
    headers={"User-Agent": "InKCre acceptance asset preparer"},
    follow_redirects=True,
    timeout=60,
  ) as response:
    response.raise_for_status()
    observed_etag = response.headers.get("ETag")
    if observed_etag is not None and observed_etag != etag:
      raise RuntimeError(f"NASA asset ETag changed for {path.name}: {observed_etag!r}")
    with temporary.open("wb") as output:
      for chunk in response.iter_bytes(1024 * 1024):
        output.write(chunk)
  observed_sha256 = _digest(temporary)
  if observed_sha256 != sha256:
    temporary.unlink(missing_ok=True)
    raise RuntimeError(f"NASA asset digest changed for {path.name}: {observed_sha256}")
  temporary.replace(path)


def _extract_frame(video_path: Path, frame_path: Path) -> None:
  if frame_path.is_file():
    return
  with av.open(str(video_path), mode="r") as container:
    stream = container.streams.video[0]
    container.seek(68 * av.time_base, backward=True)
    selected = None
    for frame in container.decode(stream):
      selected = frame
      if frame.time is not None and frame.time >= 70:
        break
    if selected is None:
      raise RuntimeError("NASA video contains no decodable frame")
    selected.to_image().save(frame_path, format="PNG")


def _extract_audio(video_path: Path, audio_path: Path) -> None:
  if audio_path.is_file():
    return
  with (
    av.open(str(video_path), mode="r") as source,
    av.open(str(audio_path), mode="w") as destination,
  ):
    output_stream = destination.add_stream("pcm_s16le", rate=16_000, layout="mono")
    resampler = AudioResampler(format="s16", layout="mono", rate=16_000)
    for frame in source.decode(audio=0):
      for converted in resampler.resample(frame):
        for packet in output_stream.encode(converted):
          destination.mux(packet)
    for converted in resampler.resample(None):
      for packet in output_stream.encode(converted):
        destination.mux(packet)
    for packet in output_stream.encode():
      destination.mux(packet)


def _remux_subtitles(video_path: Path, subtitle_path: Path, output_path: Path) -> None:
  if output_path.is_file():
    return
  with (
    av.open(str(video_path), mode="r") as source,
    av.open(str(subtitle_path), mode="r", format="webvtt") as subtitles,
    av.open(str(output_path), mode="w") as destination,
  ):
    stream_mapping = {
      stream.index: destination.add_stream_from_template(stream)
      for stream in source.streams
    }
    subtitle_input = subtitles.streams.subtitles[0]
    subtitle_output = destination.add_stream_from_template(subtitle_input)
    for packet in source.demux():
      if packet.dts is None:
        continue
      packet.stream = stream_mapping[packet.stream.index]
      destination.mux(packet)
    for packet in subtitles.demux(subtitle_input):
      if packet.dts is None:
        continue
      packet.stream = subtitle_output
      destination.mux(packet)


def prepare_assets() -> Path:
  ASSET_DIRECTORY.mkdir(parents=True, exist_ok=True)
  video_path = ASSET_DIRECTORY / "nasa-gpm-mobile.mp4"
  subtitle_path = ASSET_DIRECTORY / "nasa-gpm.vtt"
  _download(VIDEO_URL, video_path, sha256=VIDEO_SHA256, etag=VIDEO_ETAG)
  _download(
    SUBTITLE_URL,
    subtitle_path,
    sha256=SUBTITLE_SHA256,
    etag=SUBTITLE_ETAG,
  )
  _extract_frame(video_path, ASSET_DIRECTORY / "nasa-gpm-frame.png")
  _extract_audio(video_path, ASSET_DIRECTORY / "nasa-gpm-audio.wav")
  _remux_subtitles(
    video_path,
    subtitle_path,
    ASSET_DIRECTORY / "nasa-gpm-subtitled.mkv",
  )
  return ASSET_DIRECTORY


if __name__ == "__main__":
  print(prepare_assets())
