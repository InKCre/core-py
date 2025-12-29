import typing
import sqlmodel
from app.business.info_base.block import BlockManager
from app.business.info_base.relation import RelationManager
from app.engine import SessionLocal
from app.schemas.info_base.main import SubGraphForm, ArcForm
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel
from app.schemas.info_base.block import BlockID


class RootV1InsertGraphResBody(sqlmodel.SQLModel):
  blocks: tuple[BlockModel, ...]
  relations: tuple[RelationModel, ...]


class InfoBaseManager:
  """Information base manager"""

  # TODO move to routes/base.py
  @classmethod
  async def insert_subgrpah(
    cls,
    body: SubGraphForm,
  ) -> RootV1InsertGraphResBody:
    with SessionLocal() as db_session:
      await cls.add_subgraph_to_session(body, db_session)
      db_session.commit()
      inserted = cls.get_subgraph_inserted(body, db_session)
    return RootV1InsertGraphResBody(
      blocks=inserted[0],
      relations=inserted[1],
    )

  @classmethod
  async def add_subgraph_to_session(
    cls, graph: SubGraphForm, db_session: sqlmodel.Session
  ) -> None:
    if not graph.block.id:
      graph.block = await BlockManager.fetchsert(graph.block, db_session)

    if graph.out_arcs:
      for out_arc in graph.out_arcs:
        arc = ArcForm.from_out_arc(out_arc, from_subgraph=graph)
        await cls.add_arc_to_session(arc, db_session)

    if graph.in_arcs:
      for in_arc in graph.in_arcs:
        arc = ArcForm.from_in_arc(in_arc, to_subgraph=graph)
        await cls.add_arc_to_session(arc, db_session)

  @classmethod
  async def add_arc_to_session(
    cls,
    arc: "ArcForm",
    db_session: sqlmodel.Session,
  ) -> None:
    if arc.to_subgraph:
      await cls.add_subgraph_to_session(arc.to_subgraph, db_session)
      arc.relation.to_ = typing.cast(BlockID, arc.to_subgraph.block.id)
    if arc.from_subgraph:
      await cls.add_subgraph_to_session(arc.from_subgraph, db_session)
      arc.relation.from_ = typing.cast(BlockID, arc.from_subgraph.block.id)

    if not arc.relation.id:
      arc.relation = RelationManager.fetchsert(arc.relation, db_session)

  @classmethod
  def get_subgraph_inserted(
    cls,
    form: SubGraphForm,
    db_session: sqlmodel.Session,
  ) -> tuple[tuple[BlockModel, ...], tuple[RelationModel, ...]]:
    blocks = [form.block]
    relations = []
    db_session.refresh(form.block)
    if form.out_arcs:
      for out_arc in form.out_arcs:
        arc = ArcForm.from_out_arc(out_arc, from_subgraph=form)
        ibs, irs = InfoBaseManager.get_arc_inserted(arc, db_session, ignore_from=True)
        blocks.extend(ibs)
        relations.extend(irs)
    if form.in_arcs:
      for in_arc in form.in_arcs:
        arc = ArcForm.from_in_arc(in_arc, to_subgraph=form)
        ibs, irs = InfoBaseManager.get_arc_inserted(arc, db_session, ignore_to=True)
        blocks.extend(ibs)
        relations.extend(irs)
    return tuple(blocks), tuple(relations)

  @classmethod
  def get_arc_inserted(
    cls,
    arc: "ArcForm",
    db_session: sqlmodel.Session,
    ignore_from: bool = False,
    ignore_to: bool = False,
  ) -> tuple[tuple[BlockModel, ...], tuple[RelationModel, ...]]:
    """
    :param ignore_from: if True, do not include from_block
        usually when from_block is the block of the parent StarGraphForm
    :param ignore_to: if True, do not include to_block
        usually when to_block is the block of the parent StarGraphForm
    """
    blocks = []
    relations = [arc.relation]
    db_session.refresh(arc.relation)
    if arc.to_subgraph and not ignore_to:
      ibs, irs = cls.get_subgraph_inserted(arc.to_subgraph, db_session)
      blocks.extend(ibs)
      relations.extend(irs)
    if arc.from_subgraph and not ignore_from:
      ibs, irs = cls.get_subgraph_inserted(arc.from_subgraph, db_session)
      blocks.extend(ibs)
      relations.extend(irs)
    return tuple(blocks), tuple(relations)
