"""Relation Module' API Endpoints"""

__all__ = ["ROUTER"]


import fastapi

from app.business.info_base.relation import RelationManager
from app.schemas.info_base.relation import RelationCreateForm
from app.schemas.info_base.rest import RelationUpdateForm

from .entities import relation_record
from .validation import database_write


ROUTER = fastapi.APIRouter(
  prefix="/relations",
  tags=["relation"],
)


@ROUTER.post("")
def create_relation(body: RelationCreateForm) -> dict:
  with database_write():
    return relation_record(
      RelationManager.create(
        from_=body.from_,
        to_=body.to_,
        content=body.content,
      )
    )


@ROUTER.get("/by_block/{block_id}")
def get_relations_by_block(
  block_id: int,
) -> tuple[dict, ...]:
  return tuple(relation_record(item) for item in RelationManager.get(block_id=block_id))


@ROUTER.patch("/{relation_id}")
def update_relation(relation_id: int, body: RelationUpdateForm) -> dict:
  changes = body.model_dump(exclude_unset=True)
  if "from_block_id" in changes:
    changes["from_"] = changes.pop("from_block_id")
  if "to_block_id" in changes:
    changes["to_"] = changes.pop("to_block_id")
  try:
    with database_write():
      updated = RelationManager.update(relation_id, **changes)
  except ValueError as error:
    raise fastapi.HTTPException(404, str(error)) from error
  return {"type": "relation", **relation_record(updated)}


@ROUTER.delete("/{relation_id}", status_code=204)
def delete_relation(relation_id: int) -> None:
  if not RelationManager.delete(relation_id):
    raise fastapi.HTTPException(404, f"Relation {relation_id} not found")
