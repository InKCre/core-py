"""Application-owned materialization of deployment-wide Cron occurrences."""

import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import croniter  # pyrefly: ignore[untyped-import]
import pydantic
import sqlmodel

from app.business.deployment_config import DeploymentConfigManager
from app.business.job import JobManager
from app.engine import SessionLocal
from app.schemas.cron import CronID, CronModel
from app.schemas.job import JobModel, JobStatus
from libs.obsrv.main import get_logger


CRON_CONFIG_KEY = "core.cron"
CRON_CONFIG_SCHEMA_ID = "core.cron.config.v1"
LOGGER = get_logger().getChild(__name__)


class CronDeploymentConfig(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid")

  timezone: str = "UTC"

  @pydantic.field_validator("timezone")
  @classmethod
  def validate_timezone(cls, value: str) -> str:
    try:
      ZoneInfo(value)
    except ZoneInfoNotFoundError as error:
      raise ValueError("timezone must be an installed IANA timezone") from error
    return value


DeploymentConfigManager.register_schema(CRON_CONFIG_SCHEMA_ID, CronDeploymentConfig)


class CronManager:
  """Evaluate only the current minute and atomically create typed Jobs."""

  @classmethod
  def _timezone(cls) -> ZoneInfo:
    config = DeploymentConfigManager.get(CRON_CONFIG_KEY)
    if config is None:
      return ZoneInfo("UTC")
    return ZoneInfo(CronDeploymentConfig.model_validate(config).timezone)

  @classmethod
  def _database_now(cls, db_session: sqlmodel.Session) -> datetime.datetime:
    return db_session.exec(sqlmodel.select(sqlmodel.func.statement_timestamp())).one()

  @classmethod
  def _matches(cls, schedule: str, now: datetime.datetime) -> bool:
    return croniter.croniter.match(schedule, now)

  @classmethod
  def check(cls) -> int:
    """Materialize at most one Job for each matching current occurrence."""
    with SessionLocal() as discovery_session:
      cron_ids = discovery_session.exec(
        sqlmodel.select(CronModel.id).where(
          CronModel.__table__.c.enabled.is_(True)  # pyrefly: ignore[missing-attribute]
        )
      ).all()

    timezone = cls._timezone()
    created = 0
    for cron_id in cron_ids:
      if cron_id is None:
        continue
      with SessionLocal() as db_session:
        cron = db_session.exec(
          sqlmodel.select(CronModel)
          .where(CronModel.id == cron_id)
          .with_for_update(skip_locked=True)
        ).one_or_none()
        if cron is None or not cron.enabled:
          continue

        database_now = cls._database_now(db_session)
        occurrence = database_now.astimezone(datetime.UTC).replace(second=0, microsecond=0)
        local_minute = database_now.astimezone(timezone).replace(second=0, microsecond=0)
        try:
          matches = cls._matches(cron.schedule, local_minute)
        except (ValueError, KeyError):
          LOGGER.exception("Invalid persisted Cron schedule", extra={"cron_id": cron.id})
          continue
        if not matches or cron.last_scheduled_for == occurrence:
          continue

        if cron.last_job is not None:
          last_job = db_session.get(JobModel, cron.last_job)
          if last_job is not None and last_job.status in {
            JobStatus.PENDING,
            JobStatus.RUNNING,
          }:
            continue

        try:
          job = JobManager.create(
            cron.job_type,
            cron.job_parameters,
            cron.job_timeout_seconds,
            db_session=db_session,
          )
        except Exception:
          LOGGER.exception("Cron Job template is invalid", extra={"cron_id": cron.id})
          continue
        cron.last_job = job.id
        cron.last_scheduled_for = occurrence
        db_session.add(cron)
        db_session.commit()
        created += 1
    return created

  @classmethod
  def run_now(cls, cron_id: CronID) -> JobModel:
    """Create a Job from one Cron template without changing Cron progress."""
    with SessionLocal() as db_session:
      cron = db_session.get(CronModel, cron_id)
      if cron is None:
        raise ValueError(f"Cron {cron_id} does not exist")
      job = JobManager.create(
        cron.job_type,
        cron.job_parameters,
        cron.job_timeout_seconds,
        db_session=db_session,
      )
      db_session.commit()
      db_session.refresh(job)
      return job
