from .main import Resolver
import typing


class TextResolver(Resolver, rso_type="text"):
    @classmethod
    def create_brs(cls, text: str):
        from ...schemas.root import StarGraphForm
        from ...schemas.block import BlockModel

        return StarGraphForm(block=BlockModel(resolver=cls.__rsotype__, content=text))

    async def breakdown(self) -> typing.AsyncGenerator[Resolver.BorRT, Resolver.BorRT]:
        # Implementation
        ...

    async def get_text(self) -> str:
        if self._block.storage is None:
            return self._block.content
        else:
            # TODO use storage to get content
            raise NotImplementedError
