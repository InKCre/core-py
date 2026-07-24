import html2text
from .main import Resolver


class HTMLResolver(Resolver[str, str], rso_type="html"):
  @classmethod
  def create_graph(cls, url: str):
    from app.schemas.info_base.main import SubGraphForm
    from app.schemas.info_base.block import BlockModel

    return SubGraphForm(block=BlockModel(resolver=cls.__rsotype__, content=url, storage=-3))

  async def get_text(self) -> str:
    from app.business.info_base.block import BlockManager
    from app.business.info_base.relation import RelationManager

    out_relations = RelationManager.get(
      self.block_id, include_in=False, content="text content"
    )
    if out_relations:
      block = BlockManager.get(out_relations[0].to_)
      if block is not None:
        return block.content
    content = await self.get_raw_content()
    return html2text.HTML2Text().handle(content)

  async def get_str_for_embedding(self) -> str:
    """Use the rendered text as the embedding input."""
    return await self.get_text()
