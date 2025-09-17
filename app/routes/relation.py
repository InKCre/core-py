"""Relation Module' API Endpoints"""

__all__ = ["ROUTER"]


import fastapi

from app.business.relation import RelationManager
from app.schemas.relation import RelationModel


ROUTER = fastapi.APIRouter(
    prefix="/relations",
    tags=["relation"],
)


@ROUTER.post("")
def create_relation(body: RelationModel) -> RelationModel:
    return RelationManager.create(
        from_=body.from_,
        to_=body.to_,
        content=body.content,
    )


@ROUTER.get("/by_block/{block_id}")
def get_relations_by_block(
    block_id: int,
) -> tuple[RelationModel, ...]:
    return RelationManager.get(block_id=block_id)
