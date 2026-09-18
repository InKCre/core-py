"""Task-scoped Job cancellation and Cron atomicity against isolated PostgreSQL."""

import asyncio
from unittest.mock import patch
import uuid
from zoneinfo import ZoneInfo

import pydantic
import sqlalchemy

from app.business.cron import CronManager
from app.business.job import JobHandler, JobManager
from app.engine import ASYNC_DB_ENGINE, AsyncSessionFactory
from app.persistence.cron.repository import CronRepository
from app.schemas.cron import CronForm, CronModel
from app.schemas.job import JobModel, JobStatus, JobTypeModel


async def exercise():
  type_id = "task.async-job." + uuid.uuid4().hex
  entered = asyncio.Event()
  release = asyncio.Event()

  class Parameters(pydantic.BaseModel):
    pass

  class Handler(
    JobHandler[Parameters],
    job_type=type_id,
    description="Task probe",
    parameters_model=Parameters,
    default_timeout_seconds=30,
  ):
    @classmethod
    async def can_handle(cls, parameters):
      return True

    @classmethod
    async def handle(cls, job, parameters):
      entered.set()
      await release.wait()

  try:
    await JobManager.sync_job_types()
    job = await JobManager.create(type_id, {})
    assert job.id is not None
    running = asyncio.create_task(JobManager.run(job.id))
    await asyncio.wait_for(entered.wait(), 5)
    assert not await JobManager.run(job.id)
    await JobManager.abort(job.id)
    await JobManager.check_abort_requests()
    assert await running
    closed = await JobManager.get(job.id)
    assert closed is not None and closed.status == JobStatus.ABORTED
    assert closed.started_at is not None and closed.closed_at is not None
    assert job.id not in JobManager._active

    cron = await CronManager.create(CronForm(schedule="* * * * *", job_type=type_id))
    assert cron.id is not None
    materialized = await asyncio.gather(
      *(CronManager._materialize(cron.id, ZoneInfo("UTC")) for _ in range(8))
    )
    assert sum(materialized) == 1
    result = await CronManager.get(cron.id)
    assert result is not None and result.last_job is not None
    assert result.last_scheduled_for is not None

    other = await CronManager.create(CronForm(schedule="* * * * *", job_type=type_id))
    assert other.id is not None
    async with AsyncSessionFactory.begin() as session:
      before = await session.scalar(
        sqlalchemy.select(sqlalchemy.func.count())
        .select_from(JobModel)
        .where(JobModel.type == type_id)
      )
    original = CronRepository.save

    async def fail_after_flush(self, record):
      await original(self, record)
      raise RuntimeError("injected after Cron flush")

    with patch.object(CronRepository, "save", fail_after_flush):
      try:
        await CronManager._materialize(other.id, ZoneInfo("UTC"))
      except RuntimeError as error:
        assert "injected" in str(error)
      else:
        raise AssertionError("expected failure")
    async with AsyncSessionFactory.begin() as session:
      after = await session.scalar(
        sqlalchemy.select(sqlalchemy.func.count())
        .select_from(JobModel)
        .where(JobModel.type == type_id)
      )
    assert after == before
    rolled_back = await CronManager.get(other.id)
    assert rolled_back is not None and rolled_back.last_job is None
    assert rolled_back.last_scheduled_for is None
    print(
      "PASS: exclusive claim, abort closure, concurrent Cron occurrence, Job/Cron rollback"
    )
  finally:
    async with AsyncSessionFactory.begin() as session:
      await session.execute(
        sqlalchemy.delete(CronModel).where(CronModel.job_type == type_id)
      )
      await session.execute(sqlalchemy.delete(JobModel).where(JobModel.type == type_id))
      await session.execute(
        sqlalchemy.delete(JobTypeModel).where(JobTypeModel.id == type_id)
      )
    JobManager._handlers.pop(type_id, None)
    await ASYNC_DB_ENGINE.dispose()


if __name__ == "__main__":
  asyncio.run(exercise())
