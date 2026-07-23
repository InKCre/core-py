from .main import Resolver


class TextResolver(Resolver, rso_type="text"):
  """Text Resolver.

  `text` only includes characters, numbers, and punctuation. It contains no
  formatting or layout data.

  """

  @classmethod
  def create_graph(cls, text: str):
    from app.schemas.info_base.main import SubGraphForm
    from app.schemas.info_base.block import BlockModel

    return SubGraphForm(block=BlockModel(resolver=cls.__rsotype__, content=text))
