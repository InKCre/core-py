"""Exact Source command handlers hosted by the global Job runtime."""

from app.business.job import JobHandler
from app.engine import SessionLocal
from app.schemas.job import JobModel
from app.schemas.source import (
  SourceBackfillParameters,
  SourceCollectParameters,
  SourceModel,
)

from .main import SourceManager


SOURCE_COLLECT_JOB_TYPE = "core.source.collect.v1"
SOURCE_BACKFILL_JOB_TYPE = "core.source.backfill.v1"


def _source_type(parameters: SourceCollectParameters) -> str | None:
  with SessionLocal() as db_session:
    source = db_session.get(SourceModel, parameters.source)
    return None if source is None else source.type


class SourceCollectJobHandler(
  JobHandler[SourceCollectParameters],
  job_type=SOURCE_COLLECT_JOB_TYPE,
  description="Run one ordinary collection command for a configured Source.",
  parameters_model=SourceCollectParameters,
  default_timeout_seconds=300,
):
  @classmethod
  def can_handle(cls, parameters: SourceCollectParameters) -> bool:
    source_type = _source_type(parameters)
    return source_type is not None and SourceManager.has_source_type(source_type)

  @classmethod
  async def handle(cls, job: JobModel, parameters: SourceCollectParameters) -> None:
    source = SourceManager.get_source_ins(parameters.source)
    config = source.validate_collect_config(parameters.config)
    await source.collect(job, config)


class SourceBackfillJobHandler(
  JobHandler[SourceBackfillParameters],
  job_type=SOURCE_BACKFILL_JOB_TYPE,
  description="Run one exact historical collection command for a configured Source.",
  parameters_model=SourceBackfillParameters,
  default_timeout_seconds=1800,
):
  @classmethod
  def can_handle(cls, parameters: SourceBackfillParameters) -> bool:
    source_type = _source_type(parameters)
    return source_type is not None and SourceManager.supports_backfill(source_type)

  @classmethod
  async def handle(cls, job: JobModel, parameters: SourceBackfillParameters) -> None:
    source = SourceManager.get_source_ins(parameters.source)
    config = source.validate_backfill_config(parameters.config)
    await source.backfill(job, config)
