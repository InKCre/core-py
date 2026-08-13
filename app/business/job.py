"""Deep runtime for typed durable background Jobs."""

import abc
import asyncio
import typing

import jsonschema  # pyrefly: ignore[untyped-import]
import pydantic
import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlmodel

from app.engine import SessionLocal
from app.scheduler import scheduler, with_trace_id
from app.schemas.job import JobID, JobModel, JobStatus, JobTypeID, JobTypeModel
from libs.obsrv.main import get_logger


LOGGER = get_logger().getChild(__name__)
ParametersTV = typing.TypeVar("ParametersTV", bound=pydantic.BaseModel)


class JobHandler(abc.ABC, typing.Generic[ParametersTV]):
  """One exact executable Job contract registered by its owning module."""

  type: typing.ClassVar[JobTypeID]
  description: typing.ClassVar[str]
  parameters_model: typing.ClassVar[type[pydantic.BaseModel]]
  default_timeout_seconds: typing.ClassVar[int]

  def __init_subclass__(
    cls,
    *,
    job_type: JobTypeID,
    description: str,
    parameters_model: type[ParametersTV],
    default_timeout_seconds: int,
    **kwargs,
  ) -> None:
    if default_timeout_seconds <= 0:
      raise ValueError("default_timeout_seconds must be positive")
    cls.type = job_type
    cls.description = description
    cls.parameters_model = parameters_model
    cls.default_timeout_seconds = default_timeout_seconds
    JobManager.register_handler(cls)
    super().__init_subclass__(**kwargs)

  @classmethod
  def validate_parameters(cls, parameters: dict[str, typing.Any]) -> ParametersTV:
    return typing.cast(ParametersTV, cls.parameters_model.model_validate(parameters))

  @classmethod
  @abc.abstractmethod
  def can_handle(cls, parameters: ParametersTV) -> bool:
    """Return whether this runtime can execute these parameters now."""
    ...

  @classmethod
  @abc.abstractmethod
  async def handle(cls, job: JobModel, parameters: ParametersTV) -> None:
    """Execute one already claimed Job."""
    ...


class JobManager:
  """Own Job Handler registration, typed creation, claim and terminal closure."""

  _handlers: dict[JobTypeID, type[JobHandler]] = {}

  @classmethod
  def register_handler(cls, handler: type[JobHandler]) -> None:
    existing = cls._handlers.get(handler.type)
    if existing is handler:
      return
    if existing is not None:
      raise ValueError(
        f"Job type {handler.type!r} is already handled by "
        f"{existing.__module__}.{existing.__qualname__}"
      )
    cls._handlers[handler.type] = handler

  @classmethod
  def sync_job_types(cls) -> None:
    """Project locally registered exact Handler contracts to PostgreSQL."""
    with SessionLocal() as db_session:
      for handler in cls._handlers.values():
        statement = sqlalchemy.dialects.postgresql.insert(JobTypeModel).values(
          id=handler.type,
          description=handler.description,
          parameters_schema=handler.parameters_model.model_json_schema(),
          default_timeout_seconds=handler.default_timeout_seconds,
        )
        statement = statement.on_conflict_do_update(
          index_elements=[JobTypeModel.id],
          set_={
            "description": statement.excluded.description,
            "parameters_schema": statement.excluded.parameters_schema,
            "default_timeout_seconds": statement.excluded.default_timeout_seconds,
          },
        )
        db_session.exec(statement)  # type: ignore
      db_session.commit()

  @classmethod
  def _normalize_parameters(
    cls,
    job_type: JobTypeID,
    parameters: dict[str, typing.Any],
    db_session: sqlmodel.Session,
  ) -> dict[str, typing.Any]:
    handler = cls._handlers.get(job_type)
    if handler is not None:
      return handler.validate_parameters(parameters).model_dump(mode="json")

    persisted_type = db_session.get(JobTypeModel, job_type)
    if persisted_type is None:
      raise ValueError(f"Unknown Job type: {job_type}")
    jsonschema.Draft202012Validator(persisted_type.parameters_schema).validate(parameters)
    return parameters

  @classmethod
  def create(
    cls,
    job_type: JobTypeID,
    parameters: dict[str, typing.Any],
    timeout_seconds: int | None = None,
    *,
    db_session: sqlmodel.Session | None = None,
  ) -> JobModel:
    """Validate and persist one independent pending Job."""
    if db_session is None:
      with SessionLocal() as owned_session:
        job = cls.create(
          job_type,
          parameters,
          timeout_seconds,
          db_session=owned_session,
        )
        owned_session.commit()
        owned_session.refresh(job)
        return job

    normalized = cls._normalize_parameters(job_type, parameters, db_session)
    persisted_type = db_session.get(JobTypeModel, job_type)
    if persisted_type is None:
      raise ValueError(f"Unknown Job type: {job_type}")
    effective_timeout = timeout_seconds or persisted_type.default_timeout_seconds
    if effective_timeout <= 0:
      raise ValueError("Job timeout_seconds must be positive")

    job = JobModel(
      type=job_type,
      parameters=normalized,
      timeout_seconds=effective_timeout,
    )
    db_session.add(job)
    db_session.flush()
    db_session.refresh(job)
    return job

  @classmethod
  def _prepare(
    cls,
    job: JobModel,
  ) -> tuple[type[JobHandler], pydantic.BaseModel] | None:
    handler = cls._handlers.get(job.type)
    if handler is None:
      return None
    try:
      parameters = handler.validate_parameters(job.parameters)
    except pydantic.ValidationError:
      LOGGER.exception("Persisted Job parameters are invalid", extra={"job_id": job.id})
      return None
    return (handler, parameters) if handler.can_handle(parameters) else None

  @classmethod
  def _claim(cls, job_id: JobID) -> JobModel | None:
    table = typing.cast(typing.Any, getattr(JobModel, "__table__"))
    with SessionLocal() as db_session:
      statement = typing.cast(
        typing.Any,
        sqlalchemy.update(table)
        .where(table.c.id == job_id, table.c.status == JobStatus.PENDING)
        .values(status=JobStatus.RUNNING)
        .returning(table.c.id),
      )
      claimed_id = db_session.exec(statement).scalar_one_or_none()
      db_session.commit()
      return None if claimed_id is None else db_session.get(JobModel, claimed_id)

  @classmethod
  def _close(cls, job: JobModel, status: JobStatus) -> bool:
    if not status.terminal:
      raise ValueError("Job may close only to a terminal status")
    table = typing.cast(typing.Any, getattr(JobModel, "__table__"))
    with SessionLocal() as db_session:
      result = db_session.exec(
        typing.cast(
          typing.Any,
          sqlalchemy.update(table)
          .where(table.c.id == job.id, table.c.status == JobStatus.RUNNING)
          .values(
            status=status,
            state=job.state,
          ),
        )
      )
      db_session.commit()
      return bool(result.rowcount)

  @classmethod
  async def run(cls, job_id: JobID) -> bool:
    """Check local eligibility, atomically claim, then execute one Job."""
    with SessionLocal() as db_session:
      candidate = db_session.get(JobModel, job_id)
    if candidate is None:
      return False
    prepared = cls._prepare(candidate)
    if prepared is None:
      return False

    claimed = cls._claim(job_id)
    if claimed is None:
      return False
    handler, parameters = prepared
    try:
      async with asyncio.timeout(claimed.timeout_seconds):
        await handler.handle(claimed, parameters)
    except TimeoutError:
      LOGGER.warning("Job execution timed out", extra={"job_id": job_id})
      cls._close(claimed, JobStatus.TIMED_OUT)
    except Exception as error:
      LOGGER.exception("Job execution failed", extra={"job_id": job_id})
      claimed.state = {**claimed.state, "error": str(error)}
      cls._close(claimed, JobStatus.FAILED)
    else:
      cls._close(claimed, JobStatus.FINISHED)
    return True

  @classmethod
  def expire_overdue(cls) -> int:
    """Use database time to close abandoned overdue running Jobs."""
    table = typing.cast(typing.Any, getattr(JobModel, "__table__"))
    with SessionLocal() as db_session:
      result = db_session.exec(
        typing.cast(
          typing.Any,
          sqlalchemy.update(table)
          .where(
            table.c.status == JobStatus.RUNNING,
            sqlalchemy.text(
              "started_at + timeout_seconds * interval '1 second' <= statement_timestamp()"
            ),
          )
          .values(status=JobStatus.TIMED_OUT),
        )
      )
      db_session.commit()
      return result.rowcount or 0

  @classmethod
  async def check(cls) -> None:
    """Schedule locally eligible pending Jobs and converge running timeouts."""
    with SessionLocal() as db_session:
      pending = db_session.exec(
        sqlmodel.select(JobModel).where(JobModel.status == JobStatus.PENDING)
      ).all()

    for job in pending:
      if job.id is None or cls._prepare(job) is None:
        continue
      scheduler.add_job(
        func=with_trace_id(f"job.{job.id}", cls.run),
        args=[job.id],
        id=f"job.{job.id}",
        replace_existing=True,
        misfire_grace_time=None,
      )
    cls.expire_overdue()
