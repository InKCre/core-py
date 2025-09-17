from .main import Resolver


class VideoResolver(Resolver, rso_type="video"):
    @classmethod
    def create_brs(cls, url: str):
        from ...schemas.root import StarGraphForm
        from ...schemas.block import BlockModel

        return StarGraphForm(
            block=BlockModel(resolver=cls.__rsotype__, content=url, storage="URL")
        )
