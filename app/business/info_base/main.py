"""Info-base graph command coordination."""

import sqlmodel

from app.business.info_base.block import BlockManager
from app.business.info_base.relation import RelationManager
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockID, BlockModel
from app.schemas.info_base.main import (
  GraphBlockForm,
  GraphBlockIDMapping,
  GraphForm,
  GraphRelationForm,
  StarsGraphForm,
  SubmitGraphResult,
)
from app.schemas.info_base.relation import RelationModel


class InfoBaseManager:
  """Own graph-form normalization and graph insertion coordination."""

  @classmethod
  def get_related_block(
    cls,
    block_id: BlockID,
    *,
    content: str,
    outgoing: bool = True,
    db_session: sqlmodel.Session | None = None,
  ) -> BlockModel | None:
    """Return any one Block connected through the requested exact Relation.

    This singular use-facing read deliberately promises neither uniqueness nor
    ordering/repeat-read stability. Callers that care about graph multiplicity
    must query Relations directly.
    """
    if db_session is None:
      with SessionLocal() as owned_session:
        return cls.get_related_block(
          block_id,
          content=content,
          outgoing=outgoing,
          db_session=owned_session,
        )
    relation = db_session.exec(
      sqlmodel.select(RelationModel)
      .where(
        RelationModel.content == content,
        (RelationModel.from_ if outgoing else RelationModel.to_) == block_id,
      )
      .limit(1)
    ).first()
    if relation is None:
      return None
    related_id = relation.to_ if outgoing else relation.from_
    return db_session.get(BlockModel, related_id)

  @classmethod
  def normalize_graph(
    cls,
    stars: StarsGraphForm,
    id_start: int = -1,
  ) -> GraphForm:
    """Flatten recursive authoring while allocating deterministic negative IDs."""
    if id_start >= 0:
      raise ValueError("id_start must be negative")

    next_id = id_start
    blocks: list[GraphBlockForm] = []
    relations: list[GraphRelationForm] = []

    def visit(star: StarsGraphForm) -> int:
      nonlocal next_id
      block_id = next_id
      next_id -= 1
      blocks.append(GraphBlockForm.model_validate(star.block, update={"id": block_id}))

      for arc in star.out_arcs:
        to_id = visit(arc.to_graph)
        relations.append(
          GraphRelationForm.model_validate(
            arc.relation,
            update={"from_": block_id, "to_": to_id},
          )
        )
      for arc in star.in_arcs:
        from_id = visit(arc.from_graph)
        relations.append(
          GraphRelationForm.model_validate(
            arc.relation,
            update={"from_": from_id, "to_": block_id},
          )
        )
      return block_id

    visit(stars)
    return GraphForm(blocks=tuple(blocks), relations=tuple(relations))

  @classmethod
  def submit_graph(
    cls,
    graph: GraphForm,
    db_session: sqlmodel.Session | None = None,
  ) -> SubmitGraphResult:
    """Insert one validated flat graph without pre-querying positive references."""
    if db_session is None:
      with SessionLocal() as owned_session:
        result = cls.submit_graph(graph, owned_session)
        owned_session.commit()
        return result

    persisted_ids: dict[int, BlockID] = {}
    mappings: list[GraphBlockIDMapping] = []
    for form in graph.blocks:
      block = BlockManager.create(form, db_session)
      if block.id is None:  # pragma: no cover - database-generated identity invariant
        raise RuntimeError("Inserted Block is missing its database ID")
      persisted_ids[form.id] = block.id
      mappings.append(GraphBlockIDMapping(local_id=form.id, id=block.id))

    for form in graph.relations:
      RelationManager.create(
        from_=persisted_ids.get(form.from_, form.from_),
        to_=persisted_ids.get(form.to_, form.to_),
        content=form.content,
        db_session=db_session,
      )

    return SubmitGraphResult(blocks=tuple(mappings))

  @classmethod
  async def add_stars_graph_to_session(
    cls,
    graph: StarsGraphForm,
    db_session: sqlmodel.Session,
  ) -> BlockModel:
    """Persist resolver-authored recursive stars with resolver reconciliation."""
    block = await BlockManager.fetchsert(graph.block, db_session)

    for arc in graph.out_arcs:
      to_block = await cls.add_stars_graph_to_session(arc.to_graph, db_session)
      if block.id is None or to_block.id is None:
        raise RuntimeError("Persisted star Block is missing its database ID")
      relation = RelationModel.model_validate(
        arc.relation,
        update={"from_": block.id, "to_": to_block.id},
      )
      RelationManager.fetchsert(relation, db_session)

    for arc in graph.in_arcs:
      from_block = await cls.add_stars_graph_to_session(arc.from_graph, db_session)
      if block.id is None or from_block.id is None:
        raise RuntimeError("Persisted star Block is missing its database ID")
      relation = RelationModel.model_validate(
        arc.relation,
        update={"from_": from_block.id, "to_": block.id},
      )
      RelationManager.fetchsert(relation, db_session)

    return block
