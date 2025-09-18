"""LearnEnglish's Schemas"""

import typing
import sqlmodel


PoS: typing.TypeAlias = typing.Literal[
    "noun",
    "verb",
    "adjective",
    "adverb",
    "pronoun",
    "preposition",
    "conjunction",
    "interjection",
    "determiner",
    "article",
    "numeral",
    "particle",
]


class LexicalItem(sqlmodel.SQLModel):
    """Schema for lexical items like words, phrases, idioms, etc.

    Fields:
    - text: the text representation of the lexical item, a string.
    - pos: part of speech, e.g., noun, verb, adjective, etc. a string array.
    """

    text: str
    pos: list[PoS] = sqlmodel.Field(default_factory=list)
