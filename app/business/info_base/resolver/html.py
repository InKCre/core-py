import html2text
from .main import Resolver


class HTMLResolver(Resolver, rso_type="html"):
    @classmethod
    def create_graph(cls, url: str):
        from app.schemas.info_base.main import StarGraphForm
        from app.schemas.info_base.block import BlockModel

        return StarGraphForm(
            block=BlockModel(resolver=cls.__rsotype__, content=url, storage=-3)
        )

    async def get_text(self) -> str:
        from app.business.info_base.block import BlockManager
        from app.business.info_base.relation import RelationManager
        from app.business.info_base.storage import StorageManager

        out_relations = RelationManager.get(
            self._block.id, include_in=False, content="text content"
        )
        if out_relations:
            block = BlockManager.get(out_relations[0].to_)
            if block is not None:
                storage = StorageManager.new_storage(block)
                return await storage.get_content(block)
        storage = StorageManager.new_storage(self._block)
        content = await storage.get_content(self._block)
        content = html2text.HTML2Text().handle(content)
        return content
