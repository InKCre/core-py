import html2text
from app.business.block import BlockManager
from app.business.relation import RelationManager
from app.business.storage import StorageManager
from .main import Resolver


class WebpageResolver(Resolver, rso_type="webpage"):
    @classmethod
    def create_brs(cls, url: str):
        from app.schemas.root import StarGraphForm
        from app.schemas.block import BlockModel

        return StarGraphForm(
            block=BlockModel(resolver=cls.__rsotype__, content=url, storage="URL")
        )

    async def get_text(self) -> str:
        out_relations = RelationManager.get(
            self._block.id, include_in=False, content="text content"
        )
        if out_relations:
            block = BlockManager.get(out_relations[0].to_)
            if block is not None:
                storage = StorageManager.new_storage(block)
                return storage.get_content()
        storage = StorageManager.new_storage(self._block)
        content = storage.get_content()
        content = html2text.HTML2Text().handle(content)
        return content
