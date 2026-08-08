import datetime
import typing

import sqlalchemy
import sqlmodel

from app.engine import SessionLocal
from app.scheduler import scheduler, with_trace_id
from app.schemas.source import (
  SourceCollectJobID,
  SourceCollectJobModel,
  SourceCollectJobStatus,
)
from libs.obsrv.main import get_logger
from utils.datetime_ import get_datetimez

from .main import SourceManager

LOGGER = get_logger().getChild(__name__)


class SourceCollectJobManager:
  """Manager for source collect jobs."""

  @classmethod
  def create(
    cls,
    source_id: int,
    config: dict | None = None,
    *,
    db_session: sqlmodel.Session | None = None,
  ) -> SourceCollectJobModel:
    """Persist one ordinary pending collect job through the shared seam."""
    if db_session is None:
      with SessionLocal() as owned_session:
        job = cls.create(source_id, config, db_session=owned_session)
        owned_session.commit()
        owned_session.refresh(job)
        return job

    job = SourceCollectJobModel(source=source_id, config=config or {})
    db_session.add(job)
    db_session.flush()
    db_session.refresh(job)
    return job

  @classmethod
  async def create_scheduled(cls, source_id: int) -> None:
    """Create and execute the job produced by one source schedule firing."""
    job = cls.create(source_id)
    if job.id is None:
      raise RuntimeError("Persisted source collect job is missing its ID")
    await cls.run(job.id)

  @classmethod
  def _claim(cls, job_id: SourceCollectJobID) -> SourceCollectJobModel | None:
    """Atomically move one pending job to running and return its snapshot."""
    started_at = get_datetimez()
    table = typing.cast(typing.Any, getattr(SourceCollectJobModel, "__table__"))
    with SessionLocal() as db:
      statement = typing.cast(
        typing.Any,
        sqlalchemy.update(table)
        .where(
          table.c.id == job_id,
          table.c.status == SourceCollectJobStatus.PENDING,
        )
        .values(
          status=SourceCollectJobStatus.RUNNING,
          started_at=started_at,
        )
        .returning(table.c.id),
      )
      claimed_id = db.exec(statement).scalar_one_or_none()
      db.commit()
      if claimed_id is None:
        return None
      return db.exec(
        sqlmodel.select(SourceCollectJobModel).where(SourceCollectJobModel.id == claimed_id)
      ).one()

  @classmethod
  def _close(
    cls,
    job: SourceCollectJobModel,
    status: SourceCollectJobStatus,
  ) -> None:
    """Close a still-running job without reviving a timed-out execution."""
    table = typing.cast(typing.Any, getattr(SourceCollectJobModel, "__table__"))
    with SessionLocal() as db:
      statement = typing.cast(
        typing.Any,
        sqlalchemy.update(table)
        .where(
          table.c.id == job.id,
          table.c.status == SourceCollectJobStatus.RUNNING,
        )
        .values(
          status=status,
          state=job.state,
          closed_at=get_datetimez(),
        ),
      )
      db.exec(statement)
      db.commit()

  @classmethod
  async def run(cls, job_id: SourceCollectJobID) -> bool:
    """Claim and run a pending job exactly once.

    Returns ``False`` when another runner already claimed or closed the job.
    """
    job = cls._claim(job_id)
    if job is None:
      return False

    try:
      source_ins = SourceManager._get_source_ins(job.source)

      await source_ins.collect(job)
      cls._close(job, SourceCollectJobStatus.FINISHED)
    except Exception as error:
      LOGGER.error(
        "Error running source collect job",
        exc_info=True,
        extra={"job_id": job_id},
      )
      job.state = {**(job.state or {}), "error": str(error)}
      cls._close(job, SourceCollectJobStatus.FAILED)
    return True

  @classmethod
  async def check(cls):
    """Check source collect jobs
    - pending: schedule for handling
    - running: timeout check

    """
    with SessionLocal() as db:
      pending_jobs = db.exec(
        sqlmodel.select(SourceCollectJobModel).where(
          SourceCollectJobModel.status == SourceCollectJobStatus.PENDING
        )
      ).all()
      running_jobs = db.exec(
        sqlmodel.select(SourceCollectJobModel).where(
          SourceCollectJobModel.status == SourceCollectJobStatus.RUNNING
        )
      ).all()

      for job in pending_jobs:
        if job.id is None:
          continue
        # Schedule the collect
        scheduler.add_job(
          func=with_trace_id(f"source_collect_job.{job.id}", cls.run),
          args=[job.id],
          id=f"source.collect_job.{job.id}",
          replace_existing=True,
          misfire_grace_time=None,
        )
        LOGGER.info(f"Scheduled pending source collect job {job.id}")

      for job in running_jobs:
        # Check for timeout (e.g., running for more than 5 minutes)
        if (
          job.started_at is not None
          and get_datetimez() - job.started_at > datetime.timedelta(minutes=5)
        ):
          LOGGER.warning(f"Source collect job {job.id} timed out.")
          job.status = SourceCollectJobStatus.FAILED
          job.closed_at = get_datetimez()
          db.add(job)
          db.commit()
