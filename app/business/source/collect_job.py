import datetime

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
  async def run(cls, job_id: SourceCollectJobID) -> bool:
    """Atomically claim and consume one pending job at most once."""
    with SessionLocal() as db:
      job = db.exec(
        sqlmodel.select(SourceCollectJobModel)
        .where(
          SourceCollectJobModel.id == job_id,
          SourceCollectJobModel.status == SourceCollectJobStatus.PENDING,
        )
        .with_for_update(skip_locked=True)
      ).one_or_none()
      if job is None:
        return False

      job.status = SourceCollectJobStatus.RUNNING
      job.started_at = get_datetimez()
      db.add(job)
      db.commit()
      db.refresh(job)

      try:
        # Fetch source instance and run collect
        source_ins = SourceManager._get_source_ins(job.source)

        await source_ins.collect(job)
        job.status = SourceCollectJobStatus.FINISHED
      except Exception as e:
        LOGGER.error(f"Error running job {job_id}: {e}")
        job.status = SourceCollectJobStatus.FAILED
        job.state = {"error": str(e)}
      finally:
        job.closed_at = get_datetimez()
        db.add(job)
        db.commit()
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
        # Schedule the collect
        scheduler.add_job(
          func=with_trace_id(f"source_collect_job.{job.id}", cls.run),
          args=[job.id],
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
