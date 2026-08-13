import abc
import pydantic
import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlmodel
import typing
from typing import Optional as Opt

from app.engine import SessionLocal
from app.database_contract.profile import BUILTIN_SOURCE_TYPES_BY_ID
from app.business.info_base.block import BlockManager
from app.schemas.info_base.block import BlockForm, BlockModel
from app.schemas.job import JobModel
from app.schemas.source import SourceModel, SourceID, SourceTypesModel
from .resolver import SOURCE_RESOLVER_ID, SourceContent

ConfigTV = typing.TypeVar("ConfigTV", bound=pydantic.BaseModel)


class EmptySourceCommandConfig(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid")


class SourceBase(abc.ABC, typing.Generic[ConfigTV]):
  """InkCre Source Base class.

  Configuration is loaded from the database. Instantiate a source when it is
  used instead of caching configuration separately.
  """

  __configschema__: dict
  """Source configuration JSON schema"""
  __configcls__: type[ConfigTV]
  __collectconfigcls__: type[pydantic.BaseModel]
  __backfillconfigcls__: type[pydantic.BaseModel] | None

  def __init_subclass__(
    cls,
    config_cls: type[ConfigTV],
    collect_config_cls: type[pydantic.BaseModel] = EmptySourceCommandConfig,
    backfill_config_cls: type[pydantic.BaseModel] | None = None,
    **kwargs,
  ) -> None:
    # ConfigTV is bound by the concrete source subclass.
    cls.__configcls__ = config_cls  # pyrefly: ignore[no-access]
    cls.__configschema__ = config_cls.model_json_schema()
    cls.__collectconfigcls__ = collect_config_cls  # pyrefly: ignore[no-access]
    cls.__backfillconfigcls__ = backfill_config_cls  # pyrefly: ignore[no-access]
    SourceManager.add_source_type(cls)
    return super().__init_subclass__(**kwargs)

  def __init__(self, _id: SourceID) -> None:
    self._id = _id

  @abc.abstractmethod
  async def collect(self, job: JobModel, config: pydantic.BaseModel) -> None:
    """Collect new data from the source.

    :param job: The collect job containing config and state.

    Notes:
    - Should not surpress exceptions, raise it.
    """

  async def backfill(self, job: JobModel, config: pydantic.BaseModel) -> None:
    del job, config
    raise NotImplementedError(f"{self.__class__.__name__} does not support backfill")

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
      return self.__configcls__.model_validate(source.config)

  def validate_collect_config(self, config: dict) -> pydantic.BaseModel:
    return self.__collectconfigcls__.model_validate(config)

  def validate_backfill_config(self, config: dict) -> pydantic.BaseModel:
    if self.__backfillconfigcls__ is None:
      raise NotImplementedError(f"{self.__class__.__name__} does not support backfill")
    return self.__backfillconfigcls__.model_validate(config)

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
    source_classes: dict[str, type[SourceBase]] | None = None,
  ) -> None:
    """Persist registered source types during explicit runtime bootstrap."""
    registered = cls._SOURCE_CLASSES if source_classes is None else source_classes
    with SessionLocal() as db:
      for source_type, source_cls in registered.items():
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
          collect_config_schema=(
            builtin.collect_config_schema
            if builtin is not None
            else source_cls.__collectconfigcls__.model_json_schema()
          ),
          backfill_config_schema=(
            builtin.backfill_config_schema
            if builtin is not None
            else (
              None
              if source_cls.__backfillconfigcls__ is None
              else source_cls.__backfillconfigcls__.model_json_schema()
            )
          ),
        )
        stmt = stmt.on_conflict_do_update(
          index_elements=[SourceTypesModel.id],
          set_=dict(
            description=stmt.excluded.description,
            config_schema=stmt.excluded.config_schema,
            collect_config_schema=stmt.excluded.collect_config_schema,
            backfill_config_schema=stmt.excluded.backfill_config_schema,
          ),
        )
        db.exec(stmt)  # type: ignore
      db.commit()

  @classmethod
  def has_source_type(cls, source_type: str) -> bool:
    return source_type in cls._SOURCE_CLASSES

  @classmethod
  def supports_backfill(cls, source_type: str) -> bool:
    source_cls = cls._SOURCE_CLASSES.get(source_type)
    return source_cls is not None and source_cls.__backfillconfigcls__ is not None

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
      ins = source_class(_id=source_id)
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
  def create(
    cls,
    type_: str,
    nickname: Opt[str] = None,
    config: dict | None = None,
    storage: int | None = None,
  ) -> SourceModel:
    """Add a new source."""
    source_class = cls._SOURCE_CLASSES.get(type_)
    if source_class is None:
      raise ValueError(f"Source class {type_} not registered.")
    normalized = source_class.__configcls__.model_validate(config or {}).model_dump(  # pyrefly: ignore[missing-attribute]
      mode="json"
    )
    with SessionLocal() as db:
      source = SourceModel(
        type=type_,
        nickname=nickname,
        config=normalized,
        storage=storage,
      )
      db.add(source)
      db.commit()
      db.refresh(source)

    return source

  @classmethod
  def resolve_writable_storage(
    cls,
    source: SourceModel,
    db_session: sqlmodel.Session,
  ):
    from .config import resolve_writable_storage

    return resolve_writable_storage(source, db_session)

  @classmethod
  def ensure_block(
    cls,
    source: SourceModel,
    db_session: sqlmodel.Session,
  ) -> BlockModel:
    """Create/reuse and refresh one Source-owned graph anchor projection."""
    if source.id is None:
      raise ValueError("Source must be persisted before creating its anchor")
    locked = db_session.exec(
      sqlmodel.select(SourceModel).where(SourceModel.id == source.id).with_for_update()
    ).one()
    content = SourceContent(
      id=source.id,
      type=locked.type,
      nickname=locked.nickname,
    ).model_dump_json()
    if locked.block is None:
      block = BlockManager.create(
        BlockForm(resolver=SOURCE_RESOLVER_ID, content=content),
        db_session,
      )
      locked.block = block.id
      db_session.add(locked)
      db_session.flush()
      return block

    block = db_session.get(BlockModel, locked.block)
    if block is None:  # pragma: no cover - FK invariant
      raise RuntimeError("Source anchor reference does not resolve")
    if block.resolver != SOURCE_RESOLVER_ID or block.content != content:
      block.resolver = SOURCE_RESOLVER_ID
      block.storage = None
      block.content = content
      db_session.add(block)
      db_session.flush()
    return block
