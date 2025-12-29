from .main import Resolver
import typing


class TextResolver(Resolver, rso_type="text"):
  """Text Resolver.
  `text` is a string only includes characters, numbers and punctuation (no format, layout data)

  """

  @classmethod
  def create_graph(cls, text: str):
    from app.schemas.info_base.main import SubGraphForm
    from app.schemas.info_base.block import BlockModel

    return SubGraphForm(block=BlockModel(resolver=cls.__rsotype__, content=text))
