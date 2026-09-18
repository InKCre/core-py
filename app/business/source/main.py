from __future__ import annotations

import abc
import jsonschema  # pyrefly: ignore[untyped-import]
import pydantic
import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlmodel
import typing
from typing import Optional as Opt

from app.engine import SessionLocal
from app.business.info_base.block import BlockManager
from app.schemas.info_base.block import BlockForm, BlockModel
from app.schemas.job import JobModel
from app.schemas.source import SourceModel, SourceID, SourceTypesModel, SourceUpdateForm
from app.validation import input_path
from .resolver import SOURCE_RESOLVER_ID, SourceContent

ConfigTV = typing.TypeVar("ConfigTV", bound=pydantic.BaseModel)


class SourceNotFoundError(LookupError):
  """A Source instance or persisted type does not exist."""


class UnsupportedSourceCommandError(ValueError):
  """The catalog explicitly does not support the requested collection mode."""


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
        stmt = sqlalchemy.dialects.postgresql.insert(SourceTypesModel).values(
          id=source_type,
          description=source_cls.__doc__ or "No description.",
          config_schema=source_cls.__configschema__,
          collect_config_schema=source_cls.__collectconfigcls__.model_json_schema(),
          backfill_config_schema=(
            None
            if source_cls.__backfillconfigcls__ is None
            else source_cls.__backfillconfigcls__.model_json_schema()
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
  async def sync_source_types_async(
    cls, source_classes: dict[str, type[SourceBase]] | None = None
  ) -> None:
    from app.persistence.source.uow import source_uow

    registered = cls._SOURCE_CLASSES if source_classes is None else source_classes
    rows = [
      dict(
        id=source_type,
        description=source_cls.__doc__ or "No description.",
        config_schema=source_cls.__configschema__,
        collect_config_schema=source_cls.__collectconfigcls__.model_json_schema(),
        backfill_config_schema=(
          None
          if source_cls.__backfillconfigcls__ is None
          else source_cls.__backfillconfigcls__.model_json_schema()
        ),
      )
      for source_type, source_cls in registered.items()
    ]
    async with source_uow() as repository:
      await repository.sync_types(rows)

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
    with SessionLocal() as db:
      with input_path("config"):
        normalized = cls.normalize_config(type_, config or {}, db)
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
  def normalize_config(
    cls,
    type_: str,
    config: dict,
    db_session: sqlmodel.Session,
    *,
    command: typing.Literal["collect", "backfill"] | None = None,
  ) -> dict:
    """Accept catalog-only input without requiring local execution capability."""
    catalog = db_session.get(SourceTypesModel, type_)
    if catalog is None:
      raise SourceNotFoundError(f"Source type {type_!r} does not exist")
    source_class = cls._SOURCE_CLASSES.get(type_)
    if command == "backfill":
      schema = catalog.backfill_config_schema
      model = source_class.__backfillconfigcls__ if source_class else None
    elif command == "collect":
      schema = catalog.collect_config_schema
      model = source_class.__collectconfigcls__ if source_class else None
    else:
      schema = catalog.config_schema
      model = source_class.__configcls__ if source_class else None  # pyrefly: ignore[missing-attribute]
    if schema is None:
      raise UnsupportedSourceCommandError(
        f"Source type {type_!r} does not support {command}"
      )
    if model is not None:
      return model.model_validate(config).model_dump(mode="json")
    jsonschema.Draft202012Validator(schema).validate(config)
    return config

  @classmethod
  def get(cls, source_id: SourceID) -> SourceModel | None:
    with SessionLocal() as db:
      return db.get(SourceModel, source_id)

  @classmethod
  def get_type(cls, type_: str) -> SourceTypesModel | None:
    with SessionLocal() as db:
      return db.get(SourceTypesModel, type_)

  @classmethod
  def list_sources(
    cls, *, limit: int | None = None, cursor: SourceID | None = None
  ) -> tuple[list[SourceModel], SourceID | None]:
    statement = sqlmodel.select(SourceModel).order_by(sqlmodel.col(SourceModel.id))
    if cursor is not None:
      statement = statement.where(sqlmodel.col(SourceModel.id) > cursor)
    if limit is not None:
      statement = statement.limit(limit + 1)
    with SessionLocal() as db:
      rows = list(db.exec(statement).all())
    more = limit is not None and len(rows) > limit
    rows = rows[:limit]
    return rows, rows[-1].id if more else None

  @classmethod
  def list_types(
    cls, *, limit: int | None = None, cursor: str | None = None
  ) -> tuple[list[SourceTypesModel], str | None]:
    statement = sqlmodel.select(SourceTypesModel).order_by(SourceTypesModel.id)
    if cursor is not None:
      statement = statement.where(SourceTypesModel.id > cursor)
    if limit is not None:
      statement = statement.limit(limit + 1)
    with SessionLocal() as db:
      rows = list(db.exec(statement).all())
    more = limit is not None and len(rows) > limit
    rows = rows[:limit]
    return rows, rows[-1].id if more else None

  @classmethod
  def update(cls, source_id: SourceID, form: SourceUpdateForm) -> SourceModel:
    with SessionLocal() as db:
      source = db.exec(
        sqlmodel.select(SourceModel).where(SourceModel.id == source_id).with_for_update()
      ).one_or_none()
      if source is None:
        raise SourceNotFoundError(f"Source {source_id} does not exist")
      changes = form.model_dump(exclude_unset=True)
      if "config" in changes:
        with input_path("config"):
          changes["config"] = cls.normalize_config(source.type, changes["config"], db)
      for field, value in changes.items():
        setattr(source, field, value)
      db.add(source)
      if "nickname" in changes and source.block is not None:
        cls.ensure_block(source, db)
      db.commit()
      db.refresh(source)
      return source

  @classmethod
  def delete(cls, source_id: SourceID) -> bool:
    """Delete configuration only; collected graph and scheduled commands remain."""
    with SessionLocal() as db:
      source = db.get(SourceModel, source_id)
      if source is None:
        return False
      db.delete(source)
      db.commit()
    cls.SOURCES.pop(source_id, None)
    return True

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
