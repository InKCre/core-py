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

  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> LexicalItem:
    del materialize_missing
    return LexicalItem.model_validate_json(await self.get_raw_content(refresh=refresh))

  async def get_text(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    return (
      await self.get_solved_content(
        refresh=refresh,
        materialize_missing=materialize_missing,
      )
    ).text

  async def get_str_for_embedding(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    return await self.get_text(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
