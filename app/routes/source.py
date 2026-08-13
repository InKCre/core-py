"""Source Module's API Endpoints"""

__all__ = ["ROUTER"]

import fastapi
from typing import Optional as Opt
from app.business.job import JobManager
from app.business.source import SOURCE_BACKFILL_JOB_TYPE, SOURCE_COLLECT_JOB_TYPE
from app.schemas.job import JobModel
from app.schemas.source import SourceID

ROUTER = fastapi.APIRouter(
  prefix="/sources",
  tags=["source"],
)


@ROUTER.post("/{source_id}/collect")
async def run_source_collect(source_id: SourceID, body: Opt[dict] = None) -> JobModel:
  """Run source collect (by creating a source collect job.)"""
  job = JobManager.create(
    SOURCE_COLLECT_JOB_TYPE,
    {"source": source_id, "config": body or {}},
  )
  await JobManager.check()
  return job


@ROUTER.post("/{source_id}/backfill")
async def run_source_backfill(
  source_id: SourceID, body: dict, timeout_seconds: int | None = None
) -> JobModel:
  """Create one explicit historical Source Job."""
  job = JobManager.create(
    SOURCE_BACKFILL_JOB_TYPE,
    {"source": source_id, "config": body},
    timeout_seconds,
  )
  await JobManager.check()
  return job
