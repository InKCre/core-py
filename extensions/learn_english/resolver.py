"""LearnEnglish's Resolvers"""

from app.business.info_base.resolver.main import Resolver
from .schema import LexicalItem


class LexicalResolver(Resolver[LexicalItem, str], rso_type="learn_english.lexical"):
  """Resolver for english lexical like words, phrases, idioms, etc.

  Raw content is :class:`str` (JSON string).
  Solved content is :math:`schema.LexicalItem`.

  Relation of the block:
  - synonyms
  - antonyms
  - etymology
  - deliberate practice
  - in:<lang>
  """

  def __post_init__(self, raw_content=None):
    if raw_content is not None:
      self.set_solved_content(LexicalItem.model_validate_json(raw_content))

  async def get_str_for_embedding(self) -> str:
    return (await self.get_solved_content()).text
