"""Source Module's API Endpoints"""

__all__ = ["ROUTER"]

import fastapi
from typing import Optional as Opt
from app.business.source import SourceCollectJobManager
from app.schemas.source import SourceCollectJobModel, SourceID

ROUTER = fastapi.APIRouter(
  prefix="/sources",
  tags=["source"],
)


@ROUTER.post("/{source_id}/collect")
async def run_source_collect(
  source_id: SourceID, body: Opt[dict] = None
) -> SourceCollectJobModel:
  """Run source collect (by creating a source collect job.)"""
  job = SourceCollectJobManager.create(source_id, body)
  await SourceCollectJobManager.check()
  return job
