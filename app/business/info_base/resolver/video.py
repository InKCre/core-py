from .main import Resolver


class VideoResolver(Resolver, rso_type="video"):
  @classmethod
  def create_graph(cls, url: str):
    from app.schemas.info_base.main import StarGraphForm
    from app.schemas.info_base.block import BlockModel

    return StarGraphForm(
      block=BlockModel(resolver=cls.__rsotype__, content=url, storage=-2)
    )
