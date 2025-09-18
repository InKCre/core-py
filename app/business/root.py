import typing
import sqlmodel
from app.business.block import BlockManager
from app.business.relation import RelationManager
from app.engine import SessionLocal
from app.schemas.root import StarGraphForm, ArcForm
from app.schemas.block import BlockModel
from app.schemas.relation import RelationModel
from app.schemas.block import BlockID


class RootV1InsertGraphResBody(sqlmodel.SQLModel):
    blocks: tuple[BlockModel, ...]
    relations: tuple[RelationModel, ...]


class RootManager:
    """Information base manager"""

    # TODO move to routes/base.py
    @classmethod
    async def insert_grpah(
        cls,
        body: StarGraphForm,
    ) -> RootV1InsertGraphResBody:
        with SessionLocal() as db_session:
            await cls.add_star_graph_to_session(body, db_session)
            db_session.commit()
            inserted = cls.get_star_graph_inserted(body, db_session)
        return RootV1InsertGraphResBody(
            blocks=inserted[0],
            relations=inserted[1],
        )

    @classmethod
    async def add_star_graph_to_session(
        cls,
        graph: StarGraphForm,
        db_session: sqlmodel.Session,
    ) -> None:
        if not graph.block.id:
            graph.block = await BlockManager.fetchsert(graph.block, db_session)

        if graph.out_relations:
            for relation in graph.out_relations:
                relation.from_block = StarGraphForm(block=graph.block)
                await cls.add_arc_to_session(relation, db_session)

        if graph.in_relations:
            for relation in graph.in_relations:
                relation.to_block = StarGraphForm(block=graph.block)
                await cls.add_arc_to_session(relation, db_session)

    @classmethod
    async def add_arc_to_session(
        cls,
        arc: "ArcForm",
        db_session: sqlmodel.Session,
    ) -> None:
        if arc.to_block:
            await cls.add_star_graph_to_session(arc.to_block, db_session)
            arc.relation.to_ = typing.cast(BlockID, arc.to_block.block.id)
        if arc.from_block:
            await cls.add_star_graph_to_session(arc.from_block, db_session)
            arc.relation.from_ = typing.cast(BlockID, arc.from_block.block.id)

        if not arc.relation.id:
            arc.relation = RelationManager.fetchsert(arc.relation, db_session)

    @classmethod
    def get_star_graph_inserted(
        cls,
        form: StarGraphForm,
        db_session: sqlmodel.Session,
    ) -> tuple[tuple[BlockModel, ...], tuple[RelationModel, ...]]:
        blocks = [form.block]
        relations = []
        db_session.refresh(form.block)
        if form.out_relations:
            for relation in form.out_relations:
                ibs, irs = RootManager.get_arc_inserted(relation, db_session, ignore_from=True)
                blocks.extend(ibs)
                relations.extend(irs)
        if form.in_relations:
            for relation in form.in_relations:
                ibs, irs = RootManager.get_arc_inserted(relation, db_session, ignore_to=True)
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
        if arc.to_block and not ignore_to:
            ibs, irs = cls.get_star_graph_inserted(arc.to_block, db_session)
            blocks.extend(ibs)
            relations.extend(irs)
        if arc.from_block and not ignore_from:
            ibs, irs = cls.get_star_graph_inserted(arc.from_block, db_session)
            blocks.extend(ibs)
            relations.extend(irs)
        return tuple(blocks), tuple(relations)
