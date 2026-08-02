"""Exact HTML-source resolver with a derived text projection."""

import asyncio

import html2text

from .inspection import decode_html_bytes
from .main import Resolver


class HTMLResolver(Resolver[str, str | bytes], rso_type="core.html.v1"):
  @classmethod
  def create_graph(cls, url: str):
    from app.schemas.info_base.block import BlockModel
    from app.schemas.info_base.main import SubGraphForm

    return SubGraphForm(block=BlockModel(resolver=cls.__rsotype__, content=url, storage=-1))

  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    del materialize_missing
    content = await self.get_raw_content(refresh=refresh)
    return (
      content if isinstance(content, str) else decode_html_bytes(content, self.__rsotype__)
    )

  async def get_text(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    source = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    return await asyncio.to_thread(html2text.HTML2Text().handle, source)

  async def get_str_for_embedding(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    return await self.get_text(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
