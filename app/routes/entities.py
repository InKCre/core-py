"""Batch record projection, distinct from Resolver content methods."""

import typing

import fastapi

from app.business.info_base import BlockManager, RelationManager
from app.schemas.info_base.relation import RelationModel
from app.schemas.info_base.rest import EntitiesGetForm
from libs.obsrv.main import get_logger

from .content import CONTENT_RESPONSES, content_response


ROUTER = fastapi.APIRouter(tags=["info-base"])
LOGGER = get_logger().getChild(__name__)


def relation_record(relation: RelationModel) -> dict[str, typing.Any]:
  record = relation.model_dump(mode="json", exclude={"from_", "to_"})
  return {**record, "from_block_id": relation.from_, "to_block_id": relation.to_}


@ROUTER.post("/entities/get", responses=CONTENT_RESPONSES)
async def get_entities(body: EntitiesGetForm) -> fastapi.Response:
  # Shared database faults remain request failures. Only a requested entity's
  # content read can fail independently after these batch record queries.
  blocks = {
    block.id: block
    for block in BlockManager.get_many(
      [ref.id for ref in body.entities if ref.type == "block"]
    )
  }
  relations = {
    relation.id: relation
    for relation in RelationManager.get_many(
      [ref.id for ref in body.entities if ref.type == "relation"]
    )
  }
  results: list[dict[str, typing.Any]] = []
  for ref in body.entities:
    record = blocks.get(ref.id) if ref.type == "block" else relations.get(ref.id)
    correlation = ref.model_dump()
    if record is None:
      results.append(
        {
          **correlation,
          "error": {
            "code": "not_found",
            "message": f"{ref.type} {ref.id} not found",
          },
        }
      )
      continue
    if isinstance(record, RelationModel):
      projected = relation_record(record)
      if body.content == "none":
        projected.pop("content")
    else:
      projected = record.model_dump(mode="json", exclude={"content"})
      if body.content == "raw":
        projected["content"] = record.content
      elif body.content == "hydrated":
        try:
          projected["hydrated_content"] = await record.get_hydrated_content()
        except Exception as error:
          LOGGER.exception("Block hydration failed", extra={"block_id": ref.id})
          results.append(
            {
              **correlation,
              "error": {
                "code": "content_read_failed",
                "message": str(error),
              },
            }
          )
          continue
    results.append({**correlation, **projected})
  return await content_response(results)
