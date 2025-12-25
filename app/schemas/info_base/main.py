import typing
import sqlmodel
from typing import Annotated as Anno, Literal as Lit, Optional as Opt
import dataclasses
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel


Vector: typing.TypeAlias = tuple[float, ...]


@dataclasses.dataclass
class ArcForm:
    """A form for creating a relation, with its to/from block"""

    # TODO add inArcForm, outArcForm variant to reduce confusion

    relation: RelationModel
    to_block: Opt["StarGraphForm"] = None  # TODO rename, this is confusing
    """Replace relation.to_"""
    from_block: Opt["StarGraphForm"] = None
    """Replace relation.from_"""


class StarGraphForm(sqlmodel.SQLModel):
    """A form for creating a block and its relations"""

    block: BlockModel
    out_relations: tuple["ArcForm", ...] = ()
    """This block as from"""
    in_relations: tuple["ArcForm", ...] = ()  # TODO rename: this is confusing
    """This block as to"""


StarGraphForm.model_rebuild()
