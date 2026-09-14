"""Application-owned materialization of deployment-wide Cron occurrences."""

from __future__ import annotations

import datetime
import typing
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import croniter  # pyrefly: ignore[untyped-import]
import pydantic
import sqlmodel

from app.business.deployment_config import DeploymentConfigManager
from app.business.job import JobManager
from app.engine import SessionLocal
from app.schemas.cron import CronForm, CronID, CronModel, CronUpdateForm
from app.schemas.job import JobModel, JobStatus
from libs.obsrv.main import get_logger
from app.validation import input_path


CRON_CONFIG_KEY = "core.cron"
CRON_CONFIG_SCHEMA_ID = "core.cron.config.v1"
LOGGER = get_logger().getChild(__name__)


class CronNotFoundError(LookupError):
  """A Cron template does not exist."""


class InvalidCronScheduleError(ValueError):
  """A submitted schedule is not a five-field UNIX Cron expression."""


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


DeploymentConfigManager.register_schema(
  CRON_CONFIG_SCHEMA_ID, CronDeploymentConfig, keys=(CRON_CONFIG_KEY,)
)


class CronManager:
  """Evaluate only the current minute and atomically create typed Jobs."""

  @classmethod
  def _timezone(cls) -> ZoneInfo:
    config = DeploymentConfigManager.get(CRON_CONFIG_KEY)
    if config is None:
      return ZoneInfo("UTC")
    return ZoneInfo(typing.cast(CronDeploymentConfig, config).timezone)

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
        raise CronNotFoundError(f"Cron {cron_id} does not exist")
      job = JobManager.create(
        cron.job_type,
        cron.job_parameters,
        cron.job_timeout_seconds,
        db_session=db_session,
      )
      db_session.commit()
      db_session.refresh(job)
      return job

  @classmethod
  def create(cls, form: CronForm) -> CronModel:
    """Validate and create one Cron template."""
    if len(form.schedule.split()) != 5 or not croniter.croniter.is_valid(form.schedule):
      raise InvalidCronScheduleError(
        "Cron schedule must be a valid five-field UNIX expression"
      )
    with SessionLocal() as db_session:
      cron = CronModel(**form.model_dump())
      with input_path("job_parameters"):
        cron.job_parameters = JobManager.normalize_parameters(
          form.job_type, form.job_parameters, db_session
        )
      db_session.add(cron)
      db_session.commit()
      db_session.refresh(cron)
      return cron

  @classmethod
  def update(cls, cron_id: CronID, form: CronForm) -> CronModel:
    """Validate and replace the editable fields of one Cron template."""
    if len(form.schedule.split()) != 5 or not croniter.croniter.is_valid(form.schedule):
      raise InvalidCronScheduleError(
        "Cron schedule must be a valid five-field UNIX expression"
      )
    with SessionLocal() as db_session:
      cron = db_session.get(CronModel, cron_id)
      if cron is None:
        raise CronNotFoundError(f"Cron {cron_id} does not exist")
      cron.schedule = form.schedule
      cron.enabled = form.enabled
      cron.job_type = form.job_type
      with input_path("job_parameters"):
        cron.job_parameters = JobManager.normalize_parameters(
          form.job_type, form.job_parameters, db_session
        )
      cron.job_timeout_seconds = form.job_timeout_seconds
      db_session.add(cron)
      db_session.commit()
      db_session.refresh(cron)
      return cron

  @classmethod
  def get(cls, cron_id: CronID) -> CronModel | None:
    with SessionLocal() as db:
      return db.get(CronModel, cron_id)

  @classmethod
  def list_crons(
    cls, *, limit: int | None = None, cursor: CronID | None = None
  ) -> tuple[list[CronModel], CronID | None]:
    statement = sqlmodel.select(CronModel).order_by(sqlmodel.col(CronModel.id))
    if cursor is not None:
      statement = statement.where(sqlmodel.col(CronModel.id) > cursor)
    if limit is not None:
      statement = statement.limit(limit + 1)
    with SessionLocal() as db:
      rows = list(db.exec(statement).all())
    more = limit is not None and len(rows) > limit
    rows = rows[:limit]
    return rows, rows[-1].id if more else None

  @classmethod
  def patch(cls, cron_id: CronID, form: CronUpdateForm) -> CronModel:
    with SessionLocal() as db:
      cron = db.exec(
        sqlmodel.select(CronModel).where(CronModel.id == cron_id).with_for_update()
      ).one_or_none()
      if cron is None:
        raise CronNotFoundError(f"Cron {cron_id} does not exist")
      changes = form.model_dump(exclude_unset=True)
      candidate = CronForm.model_validate(
        {
          **{field: getattr(cron, field) for field in CronForm.model_fields},
          **changes,
        }
      )
      if len(candidate.schedule.split()) != 5 or not croniter.croniter.is_valid(
        candidate.schedule
      ):
        raise InvalidCronScheduleError(
          "Cron schedule must be a valid five-field UNIX expression"
        )
      with input_path("job_parameters"):
        parameters = JobManager.normalize_parameters(
          candidate.job_type, candidate.job_parameters, db
        )
      for field in changes:
        setattr(cron, field, getattr(candidate, field))
      cron.job_parameters = parameters
      db.add(cron)
      db.commit()
      db.refresh(cron)
      return cron

  @classmethod
  def delete(cls, cron_id: CronID) -> bool:
    with SessionLocal() as db:
      cron = db.get(CronModel, cron_id)
      if cron is None:
        return False
      db.delete(cron)
      db.commit()
      return True
