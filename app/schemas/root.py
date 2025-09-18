import typing
import sqlmodel
from typing import Annotated as Anno, Literal as Lit, Optional as Opt
import dataclasses
from app.schemas.block import BlockModel
from app.schemas.relation import RelationModel


Vector: typing.TypeAlias = tuple[float, ...]


@dataclasses.dataclass
class ArcForm:
    """A form for creating a relation, with its to/from block"""

    relation: RelationModel
    to_block: Opt["StarGraphForm"] = None
    """Replace relation.to_"""
    from_block: Opt["StarGraphForm"] = None
    """Replace relation.from_"""


class StarGraphForm(sqlmodel.SQLModel):
    """A form for creating a block and its relations"""

    block: BlockModel
    out_relations: tuple["ArcForm", ...] = ()
    """This block as from"""
    in_relations: tuple["ArcForm", ...] = ()
    """This block as to"""


StarGraphForm.model_rebuild()
