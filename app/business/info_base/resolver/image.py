"""Exact image resolver using bounded Pillow header inspection."""

import asyncio
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, UnidentifiedImageError

from app.schemas.info_base.block import BlockForm
from app.schemas.info_base.main import OutArcForm, StarsGraphForm
from app.schemas.info_base.relation import RelationForm

from .contracts import ResolverContentError, UnsupportedResolverCapability
from .inspection import ByteContentFacts, detect_media_type, require_bytes
from .main import Resolver


@dataclass(frozen=True, slots=True)
class ImageSolvedContent(ByteContentFacts):
  format: str | None
  width: int | None
  height: int | None
  frame_count: int | None


def _inspect_image(content: bytes) -> ImageSolvedContent:
  try:
    with Image.open(BytesIO(content)) as image:
      image_format = image.format.lower() if image.format else None
      width, height = image.size
      frame_count = getattr(image, "n_frames", None)
      image.verify()
  except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as error:
    raise ResolverContentError("core.image.v1", "invalid image") from error
  return ImageSolvedContent(
    content=content,
    byte_size=len(content),
    detected_media_type=detect_media_type(content),
    format=image_format,
    width=width,
    height=height,
    frame_count=frame_count,
  )


class ImageResolver(
  Resolver[ImageSolvedContent, bytes],
  rso_type="core.image.v1",
):
  @classmethod
  def create_graph(cls, url: str, alt_text: str | None = None) -> StarsGraphForm:
    from .text import TextResolver

    return StarsGraphForm(
      block=BlockForm(resolver=cls.__rsotype__, content=url, storage=-1),
      out_arcs=(
        OutArcForm(
          relation=RelationForm(content="alt:text"),
          to_graph=TextResolver.create_graph(alt_text),
        ),
      )
      if alt_text
      else (),
    )

  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> ImageSolvedContent:
    del materialize_missing
    content = require_bytes(
      await self.get_raw_content(refresh=refresh),
      self.__rsotype__,
    )
    return await asyncio.to_thread(_inspect_image, content)

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
    return "image"
