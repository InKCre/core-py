"""LearnEnglish's Resolvers"""

import json
from app.business.resolver.main import Resolver
from .schema import LexicalItem


class LexicalResolver(Resolver, rso_type="learn_english.lexical"):
    """Resolver for english lexical like words, phrases, idioms, etc.


    Block content is a :math:`schema.LexicalItem`.

    Relation of the block:
    - synonyms
    - antonyms
    - etymology
    - deliberate practice
    - in:<lang>
    """

    def __post_init__(self):
        self._content = LexicalItem(**json.loads(self._block.content))

    def get_str_for_embedding(self) -> str:
        return self._content.text
