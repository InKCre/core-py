import abc
import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlmodel
import typing
from typing import Optional as Opt

from app.engine import SessionLocal
from app.schemas.info_base.block import BlockID
from app.schemas.source import SourceModel, SourceID, SourceTypesModel
from app.scheduler import scheduler

if typing.TYPE_CHECKING:
  from collect_job import SourceCollectJobModel

ConfigTV = typing.TypeVar("ConfigTV", bound=sqlmodel.SQLModel)


class SourceBase(abc.ABC, typing.Generic[ConfigTV]):
  """InkCre Source Base class.

  Configuration is loaded from the database. Instantiate a source when it is
  used instead of caching configuration separately.
  """

  __configschema__: dict
  """Source configuration JSON schema"""
  __configcls__: type[ConfigTV]

  def __init_subclass__(cls, config_cls: type[ConfigTV], **kwargs) -> None:
    cls.__configcls__ = config_cls
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

  def get_config(self) -> ConfigTV:
    """Get the configuration of the source."""
    with SessionLocal() as db:
      source = db.exec(sqlmodel.select(SourceModel).where(SourceModel.id == self._id)).one()
      return typing.cast(ConfigTV, self.__configcls__.model_validate(source.config))

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

  @classmethod
  def add_source_type(cls, source_cls: type[SourceBase]) -> None:
    """Register a source type in memory without external side effects."""
    source_type = source_cls.__module__ + "." + source_cls.__qualname__
    cls._SOURCE_CLASSES[source_type] = source_cls

  @classmethod
  def sync_source_types(cls) -> None:
    """Persist registered source types during explicit runtime bootstrap."""
    with SessionLocal() as db:
      for source_type, source_cls in cls._SOURCE_CLASSES.items():
        stmt = sqlalchemy.dialects.postgresql.insert(SourceTypesModel).values(
          id=source_type,
          description=source_cls.__doc__ or "No description.",
          config_schema=source_cls.__configschema__,
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
  def set_up_collect_jobs(cls):
    with SessionLocal() as db:
      sources = db.exec(
        sqlmodel.select(SourceModel).where(SourceModel.collect_at is not None)
      ).all()

    for source in sources:
      if source.collect_at is None:
        continue
      # TODO create a source collect job instead of directly scheduling the collect
      scheduler.add_job(
        func=cls._get_source_ins(typing.cast(SourceID, source.id), source.type).collect,
        trigger=source.collect_at.to_trigger(),
        id=f"source.{source.id}.collect",
        replace_existing=True,
        misfire_grace_time=None,
      )

  @classmethod
  def _get_source_ins(cls, source_id: SourceID, source_type: Opt[str] = None) -> SourceBase:
    ins = cls.SOURCES.get(source_id, None)
    if ins is None:
      if source_type is None:
        with SessionLocal() as db:
          source_type = db.exec(
            sqlmodel.select(SourceModel.type).where(SourceModel.id == source_id)
          ).one()
      source_class = cls._SOURCE_CLASSES.get(source_type, None)
      if source_class is None:
        raise ValueError(f"Source class {source_type} not registered.")
      ins = source_class(_id=typing.cast(SourceID, source_id))
      cls.SOURCES[source_id] = ins
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

    return source
