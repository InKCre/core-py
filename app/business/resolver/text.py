from .main import Resolver
import typing


class TextResolver(Resolver, rso_type="text"):
    @classmethod
    def create_graph(cls, text: str):
        from app.schemas.root import StarGraphForm
        from app.schemas.block import BlockModel

        return StarGraphForm(block=BlockModel(resolver=cls.__rsotype__, content=text))

    async def breakdown(self) -> typing.AsyncGenerator[Resolver.BorRT, Resolver.BorRT]:
        # Implementation
        ...
