__all__ = [
  "Vector",
  "ArcForm",
  "OutArcForm",
  "InArcForm",
  "SubGraphForm",
]

import typing
import sqlmodel
from typing import Optional as Opt
import dataclasses
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel


Vector: typing.TypeAlias = tuple[float, ...]


@dataclasses.dataclass
class OutArcForm:
  """A form for creating an outgoing arc"""

  relation: RelationModel
  to_subgraph: "SubGraphForm"
  """The block will be relation.to_"""


@dataclasses.dataclass
class InArcForm:
  """A form for creating an incoming arc"""

  relation: RelationModel
  from_subgraph: "SubGraphForm"
  """The block will be relation.from_"""


@dataclasses.dataclass
class ArcForm:
  """A form for an arc (to block, relation, from block)"""

  relation: RelationModel
  to_subgraph: Opt["SubGraphForm"] = None
  """The block will be relation.to_"""
  from_subgraph: Opt["SubGraphForm"] = None
  """The block will be relation.from_"""

  @classmethod
  def from_out_arc(
    cls,
    out_arc: OutArcForm,
    from_subgraph: Opt["SubGraphForm"] = None,
  ) -> "ArcForm":
    """Create ArcForm from OutArcForm"""
    return cls(
      relation=out_arc.relation,
      to_subgraph=out_arc.to_subgraph,
      from_subgraph=from_subgraph,
    )

  @classmethod
  def from_in_arc(
    cls,
    in_arc: InArcForm,
    to_subgraph: Opt["SubGraphForm"] = None,
  ) -> "ArcForm":
    """Create ArcForm from InArcForm"""
    return cls(
      relation=in_arc.relation,
      from_subgraph=in_arc.from_subgraph,
      to_subgraph=to_subgraph,
    )


class SubGraphForm(sqlmodel.SQLModel):
  """A form for creating a sub-graph (start from a block, follows its in/out relations,
  includes all reachable blocks)
  """

  block: BlockModel
  out_arcs: tuple["OutArcForm", ...] = ()
  """This block as from"""
  in_arcs: tuple["InArcForm", ...] = ()
  """This block as to"""


SubGraphForm.model_rebuild()
