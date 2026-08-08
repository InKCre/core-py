"""LearnEnglish's Resolvers"""

from app.business.info_base.resolver.label import format_label
from app.business.info_base.resolver.main import Resolver
from app.schemas.info_base.block import BlockForm
from app.schemas.info_base.main import StarsGraphForm

from .schema import LexicalItem


class LexicalResolver(
  Resolver[LexicalItem, str],
  rso_type="extensions.learn_english.lexical.v1",
):
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

  draft_description = (
    "Create one English lexical item such as a word, phrase, or idiom, "
    "with optional parts of speech."
  )
  draft_input_model = LexicalItem

  @classmethod
  def create_graph(cls, input: LexicalItem) -> StarsGraphForm:
    return StarsGraphForm(
      block=BlockForm(
        resolver=cls.__rsotype__,
        content=input.model_dump_json(),
      )
    )

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

  async def get_label(self, *, refresh: bool = False) -> str:
    content = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=False,
    )
    return format_label("lexical item", content.text)
