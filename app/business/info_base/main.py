"""Info-base graph command coordination."""

from app.schemas.info_base.main import (
  GraphBlockForm,
  GraphForm,
  GraphRelationForm,
  StarsGraphForm,
)


class InfoBaseManager:
  """Own graph-form normalization and graph insertion coordination."""

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
