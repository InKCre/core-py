import abc
from collections.abc import Collection, Mapping
from dataclasses import dataclass
import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlmodel
import typing
from typing import Optional as Opt

from app.engine import SessionLocal
from app.database_contract.profile import BUILTIN_SOURCE_TYPES_BY_ID
from app.schemas.info_base.block import BlockID
from app.schemas.source import (
  CollectAt,
  SourceCollectJobModel,
  SourceModel,
  SourceID,
  SourceTypesModel,
)
from app.scheduler import scheduler

if typing.TYPE_CHECKING:
  from .collect_job import SourceCollectJobModel

ConfigTV = typing.TypeVar("ConfigTV", bound=sqlmodel.SQLModel)


@dataclass(frozen=True)
class SourceRuntimeActivation:
  """Exact scheduler/cache contribution owned by one runtime publication."""

  source_types: frozenset[str]
  source_ids: tuple[SourceID, ...]
  job_ids: tuple[str, ...]


class SourceBase(abc.ABC, typing.Generic[ConfigTV]):
  """InkCre Source Base class.

  Configuration is loaded from the database. Instantiate a source when it is
  used instead of caching configuration separately.
  """

  __configschema__: dict
  """Source configuration JSON schema"""
  __configcls__: type[ConfigTV]

  def __init_subclass__(cls, config_cls: type[ConfigTV], **kwargs) -> None:
    # ConfigTV is bound by the concrete source subclass.
    cls.__configcls__ = config_cls  # pyrefly: ignore[no-access]
    cls.__configschema__ = config_cls.model_json_schema()
    SourceManager.add_source_type(cls)
    return super().__init_subclass__(**kwargs)

  def __init__(self, _id: SourceID) -> None:
    self._id = _id

  @abc.abstractmethod
  async def collect(self, job: "SourceCollectJobModel") -> None:
    """Collect new data from the source.

    :param job: The collect job containing config and state.

    Notes:
    - Should not surpress exceptions, raise it.
    """

  @abc.abstractmethod
  async def _organize(self, block_id: BlockID) -> None:
    """Organize the collected block.

    Organization to collected blocks are concurrently.
    """

  async def record(self, data: typing.Any) -> None:
    """Record data passively (e.g., from webhook).

    :param data: The data to record from external source (e.g., webhook payload).

    Notes:
    - Should not suppress exceptions, raise it.
    - Used for passive collection methods like webhooks.
    """
    raise NotImplementedError(f"{self.__class__.__name__} does not support passive record")

  def scheduled_collect_config(self) -> dict[str, typing.Any]:
    """Build immutable input for a scheduler-created collect job."""
    return {}

  def get_config(self) -> ConfigTV:
    """Get the configuration of the source."""
    with SessionLocal() as db:
      source = db.exec(sqlmodel.select(SourceModel).where(SourceModel.id == self._id)).one()
      return self.__configcls__.model_validate(source.config)

  def get_state(self) -> dict:
    """Get the source state from database."""
    with SessionLocal() as db:
      source = db.exec(sqlmodel.select(SourceModel).where(SourceModel.id == self._id)).one()
      return source.state or {}

  def set_state(self, state: dict) -> None:
    """Save the source state to database."""
    with SessionLocal() as db:
      source = db.exec(sqlmodel.select(SourceModel).where(SourceModel.id == self._id)).one()
      source.state = state
      db.add(source)
      db.commit()


class SourceManager:
  """

  - Run collect method of all configured sources
  - Add, remove and configure source instances
  - Add, remove sources
  """

  SOURCES: dict[SourceID, SourceBase] = {}
  _SOURCE_CLASSES: dict[str, type[SourceBase]] = {}
  _SOURCE_ROW_TYPES: dict[SourceID, str] = {}
  _SOURCE_INSTANCE_TYPES: dict[SourceID, str] = {}
  _SOURCE_JOB_TYPES: dict[str, str] = {}

  @classmethod
  def snapshot_source_types(cls) -> dict[str, type[SourceBase]]:
    """Capture the in-memory source publication surface.

    Extension startup uses this snapshot to build a reversible publication
    handle. Importing a source remains memory-only; persistence still happens
    only through :meth:`sync_source_types`.
    """
    return dict(cls._SOURCE_CLASSES)

  @classmethod
  def restore_source_types(
    cls,
    before: dict[str, type[SourceBase]],
    published: dict[str, type[SourceBase]],
  ) -> None:
    """Undo only source registrations made by one publication.

    A later publisher that replaced the same key wins; this avoids one
    extension teardown erasing an unrelated, newer registration.
    """
    missing = object()
    for source_type in before.keys() | published.keys():
      previous = before.get(source_type, missing)
      publication = published.get(source_type, missing)
      if previous is publication:
        continue

      current = cls._SOURCE_CLASSES.get(source_type, missing)
      if current is not publication:
        continue
      if previous is missing:
        cls._SOURCE_CLASSES.pop(source_type, None)
      else:
        cls._SOURCE_CLASSES[source_type] = typing.cast(type[SourceBase], previous)

  @classmethod
  def add_source_type(cls, source_cls: type[SourceBase]) -> None:
    """Register a source type in memory without external side effects."""
    source_type = source_cls.__module__ + "." + source_cls.__qualname__
    cls._SOURCE_CLASSES[source_type] = source_cls

  @classmethod
  def sync_source_types(
    cls,
    source_types: Mapping[str, type[SourceBase]] | None = None,
  ) -> None:
    """Persist registered source types during explicit runtime bootstrap."""
    selected = source_types if source_types is not None else cls._SOURCE_CLASSES
    with SessionLocal() as db:
      for source_type, source_cls in selected.items():
        builtin = BUILTIN_SOURCE_TYPES_BY_ID.get(source_type)
        stmt = sqlalchemy.dialects.postgresql.insert(SourceTypesModel).values(
          id=source_type,
          description=(
            builtin.description
            if builtin is not None
            else source_cls.__doc__ or "No description."
          ),
          config_schema=(
            builtin.config_schema if builtin is not None else source_cls.__configschema__
          ),
        )
        stmt = stmt.on_conflict_do_update(
          index_elements=[SourceTypesModel.id],
          set_=dict(
            description=stmt.excluded.description,
            config_schema=stmt.excluded.config_schema,
          ),
        )
        db.exec(stmt)  # type: ignore
      db.commit()

  @classmethod
  def _source_rows(
    cls,
    source_types: Collection[str] | None = None,
  ) -> tuple[SourceModel, ...]:
    with SessionLocal() as db:
      statement = sqlmodel.select(SourceModel)
      if source_types is not None:
        if not source_types:
          return ()
        statement = statement.where(sqlmodel.col(SourceModel.type).in_(tuple(source_types)))
      return tuple(db.exec(statement).all())

  @classmethod
  def set_up_collect_jobs(
    cls,
    source_types: Collection[str] | None = None,
  ) -> SourceRuntimeActivation:
    sources = cls._source_rows(source_types)
    source_ids = tuple(source.id for source in sources if source.id is not None)
    cls._SOURCE_ROW_TYPES.update(
      {source.id: source.type for source in sources if source.id is not None}
    )
    job_ids: list[str] = []

    try:
      for source in sources:
        if source.collect_at is None or source.id is None:
          continue
        job_id = f"source.{source.id}.collect"
        scheduler.add_job(
          func=cls._run_scheduled_collect,
          args=[source.id],
          trigger=source.collect_at.to_trigger(),
          id=job_id,
          replace_existing=True,
          misfire_grace_time=None,
        )
        job_ids.append(job_id)
        cls._SOURCE_JOB_TYPES[job_id] = source.type
    except Exception:
      cls.withdraw_runtime_activation(
        SourceRuntimeActivation(
          source_types=frozenset(source_types or (source.type for source in sources)),
          source_ids=source_ids,
          job_ids=tuple(job_ids),
        )
      )
      raise
    return SourceRuntimeActivation(
      source_types=frozenset(source_types or (source.type for source in sources)),
      source_ids=source_ids,
      job_ids=tuple(job_ids),
    )

  @classmethod
  def withdraw_runtime_activation(cls, activation: SourceRuntimeActivation) -> None:
    """Remove an exact runtime contribution without querying or deleting rows."""
    job_ids = set(activation.job_ids)
    job_ids.update(
      job_id
      for job_id, source_type in cls._SOURCE_JOB_TYPES.items()
      if source_type in activation.source_types
    )
    for job_id in job_ids:
      if scheduler.get_job(job_id) is not None:
        scheduler.remove_job(job_id)
      cls._SOURCE_JOB_TYPES.pop(job_id, None)

    source_ids = set(activation.source_ids)
    source_ids.update(
      source_id
      for source_id, source_type in cls._SOURCE_ROW_TYPES.items()
      if source_type in activation.source_types
    )
    source_ids.update(
      source_id
      for source_id, source_type in cls._SOURCE_INSTANCE_TYPES.items()
      if source_type in activation.source_types
    )
    source_ids.update(
      source_id
      for source_id, source in cls.SOURCES.items()
      if f"{type(source).__module__}.{type(source).__qualname__}" in activation.source_types
    )
    for source_id in source_ids:
      cls.SOURCES.pop(source_id, None)
      cls._SOURCE_ROW_TYPES.pop(source_id, None)
      cls._SOURCE_INSTANCE_TYPES.pop(source_id, None)

  @classmethod
  async def _run_scheduled_collect(cls, source_id: SourceID) -> None:
    """Create one durable collect job, then run the canonical job path."""
    from .collect_job import SourceCollectJobManager

    source = cls._get_source_ins(source_id)
    with SessionLocal() as db:
      job = SourceCollectJobModel(
        source=source_id,
        config=source.scheduled_collect_config(),
      )
      db.add(job)
      db.commit()
      db.refresh(job)
      if job.id is None:
        raise RuntimeError("Scheduled Source collect job did not receive an ID")
      job_id = job.id
    await SourceCollectJobManager.run(job_id)

  @classmethod
  def _get_source_ins(cls, source_id: SourceID, source_type: Opt[str] = None) -> SourceBase:
    ins = cls.SOURCES.get(source_id, None)
    if ins is None:
      if source_type is None:
        source_type = cls._SOURCE_ROW_TYPES.get(source_id)
      if source_type is None:
        with SessionLocal() as db:
          source_type = db.exec(
            sqlmodel.select(SourceModel.type).where(SourceModel.id == source_id)
          ).one()
      source_class = cls._SOURCE_CLASSES.get(source_type, None)
      if source_class is None:
        raise ValueError(f"Source class {source_type} not registered.")
      ins = source_class(_id=source_id)
      cls.SOURCES[source_id] = ins
      cls._SOURCE_ROW_TYPES[source_id] = source_type
      cls._SOURCE_INSTANCE_TYPES[source_id] = source_type
    elif source_type is not None:
      cls._SOURCE_INSTANCE_TYPES.setdefault(source_id, source_type)
    return ins

  @classmethod
  def get_source_ins(cls, source_id: SourceID) -> SourceBase:
    """Get source instance by ID.

    :param source_id: The source ID
    :return: Source instance
    """
    return cls._get_source_ins(source_id)

  @classmethod
  def create(cls, type_: str, nickname: Opt[str] = None) -> SourceModel:
    """Add a new source."""
    with SessionLocal() as db:
      source = SourceModel(type=type_, nickname=nickname)
      db.add(source)
      db.commit()
      db.refresh(source)

    if source.id is not None:
      cls._SOURCE_ROW_TYPES[source.id] = type_

    return source

  @classmethod
  def ensure_exists(
    cls,
    type_: str,
    *,
    nickname: Opt[str] = None,
    config: dict | None = None,
    collect_at: CollectAt | None = None,
  ) -> tuple[SourceModel, bool]:
    """Return any existing Source of this type, or atomically create one.

    This is an at-least-one primitive, not a uniqueness policy: existing Sources
    are never renamed or rescheduled, and callers may still create more Sources.
    """
    with SessionLocal() as db:
      db.connection().execute(
        sqlalchemy.text("SELECT pg_advisory_xact_lock(hashtextextended(:type, 0))"),
        {"type": type_},
      )
      source = db.exec(
        sqlmodel.select(SourceModel)
        .where(SourceModel.type == type_)
        .order_by(sqlmodel.col(SourceModel.id))
        .limit(1)
        .with_for_update()
      ).one_or_none()
      created = source is None
      if source is None:
        source = SourceModel(
          type=type_,
          nickname=nickname,
          config=dict(config or {}),
          collect_at=collect_at,
        )
        db.add(source)
        db.commit()
        db.refresh(source)

    if source.id is not None:
      cls._SOURCE_ROW_TYPES[source.id] = type_
    if created and source.collect_at is not None:
      cls.set_up_collect_jobs({type_})
    return source, created
