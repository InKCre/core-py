"""Source Module's API Endpoints"""

__all__ = ["ROUTER"]

import fastapi
from typing import Optional as Opt
from app.business.source import SourceCollectJobManager
from app.engine import SessionLocal
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
  with SessionLocal() as db:
    if body is None:
      body = {}
    job = SourceCollectJobModel(source=source_id, config=body)
    db.add(job)
    db.commit()
    db.refresh(job)

  await SourceCollectJobManager.check()
  return job
