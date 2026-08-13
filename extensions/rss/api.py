"""Extension APIs for explicit RSS application commands."""

from __future__ import annotations

import dataclasses

import fastapi
import pydantic

from app.business.info_base.block import BlockManager
from app.business.info_base.resolver import ResolverManager

from .resolver import EnclosureResolver


class MaterializeEnclosuresRequest(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid")

  enclosure_block_ids: tuple[int, ...] = pydantic.Field(min_length=1)
  target_storage_id: int = -4


class MaterializeEnclosureResult(pydantic.BaseModel):
  enclosure_block_id: int
  content_block_id: int | None = None
  status: str
  resolver_id: str | None = None
  error: str | None = None


class MaterializeEnclosuresResponse(pydantic.BaseModel):
  results: tuple[MaterializeEnclosureResult, ...]


def register_api(router: fastapi.APIRouter) -> None:
  @router.post("/enclosures/materialize")
  async def materialize_enclosures(
    body: MaterializeEnclosuresRequest,
  ) -> MaterializeEnclosuresResponse:
    results: list[MaterializeEnclosureResult] = []
    for enclosure_block_id in body.enclosure_block_ids:
      try:
        block = BlockManager.get(enclosure_block_id)
        if block is None:
          raise LookupError(f"enclosure block {enclosure_block_id} not found")
        resolver = ResolverManager.get(block)
        if not isinstance(resolver, EnclosureResolver):
          raise TypeError(f"block {enclosure_block_id} is not an RSS enclosure")
        result = await resolver.materialize_content(
          target_storage_id=body.target_storage_id
        )
        results.append(MaterializeEnclosureResult(**dataclasses.asdict(result)))
      except Exception as error:
        results.append(
          MaterializeEnclosureResult(
            enclosure_block_id=enclosure_block_id,
            status="failed",
            error=str(error),
          )
        )
    return MaterializeEnclosuresResponse(results=tuple(results))


__all__ = [
  "MaterializeEnclosureResult",
  "MaterializeEnclosuresRequest",
  "MaterializeEnclosuresResponse",
  "register_api",
]
