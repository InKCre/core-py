__all__ = [
  "StorageManager",
  "Storage",
]

import abc
import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlmodel
import typing
from typing import Optional as Opt
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.storage import StorageID, StorageModel, StorageTypesModel


ConfigTV = typing.TypeVar("ConfigTV", bound=sqlmodel.SQLModel)


class _EmptyConfig(sqlmodel.SQLModel):
  """Default empty config class for storages without configuration."""

  pass


class StorageManager:
  STORAGES: dict[StorageID, "Storage"] = {}
  """Instance cache: StorageID -> Storage instance"""

  _STORAGE_CLASSES: dict[str, type["Storage"]] = {}
  """Storage type registry: type string -> Storage class"""

  @classmethod
  def add_storage_type(cls, storage_cls: type["Storage"]) -> None:
    """Register a new storage type using PostgreSQL upsert."""
    storage_type = storage_cls.__module__ + "." + storage_cls.__qualname__
    cls._STORAGE_CLASSES[storage_type] = storage_cls

    stmt = sqlalchemy.dialects.postgresql.insert(StorageTypesModel).values(
      id=storage_type,
      description=storage_cls.__doc__ or "No description.",
      config_schema=storage_cls.__configschema__,
    )
    stmt = stmt.on_conflict_do_update(
      index_elements=[StorageTypesModel.id],
      set_=dict(
        description=stmt.excluded.description,
        config_schema=stmt.excluded.config_schema,
      ),
    )

    with SessionLocal() as db:
      db.exec(stmt)  # type: ignore
      db.commit()

  @classmethod
  def register_storage(cls, storage_cls: type["Storage"]):
    """Register a storage class (called by __init_subclass__)."""
    storage_type = storage_cls.__module__ + "." + storage_cls.__qualname__
    cls._STORAGE_CLASSES[storage_type] = storage_cls

  @classmethod
  def _get_storage_ins(
    cls, storage_id: StorageID, storage_type: Opt[str] = None
  ) -> "Storage":
    """Get or create a storage instance from the cache."""
    ins = cls.STORAGES.get(storage_id, None)
    if ins is None:
      if storage_type is None:
        with SessionLocal() as db:
          storage_type = db.exec(
            sqlmodel.select(StorageModel.type).where(StorageModel.id == storage_id)
          ).one()
      storage_class = cls._STORAGE_CLASSES.get(storage_type)
      if storage_class is None:
        raise ValueError(f"Storage class {storage_type} not registered.")

      # Get storage record to pass to constructor
      with SessionLocal() as db:
        storage_record = db.exec(
          sqlmodel.select(StorageModel).where(StorageModel.id == storage_id)
        ).one()

      ins = storage_class(storage_record)
      cls.STORAGES[storage_id] = ins
    return ins

  @classmethod
  def new_storage(cls, block: BlockModel) -> "Storage":
    """Create storage instance from block."""
    if block.storage is None:
      return Storage(None)

    storage_id = typing.cast(StorageID, block.storage)
    return cls._get_storage_ins(storage_id)

  @classmethod
  def create(
    cls,
    type_: str,
    nickname: Opt[str] = None,
    config: Opt[dict] = None,
  ) -> StorageModel:
    """Create a new storage instance."""
    with SessionLocal() as db:
      storage = StorageModel(type=type_, nickname=nickname, config=config or {})
      db.add(storage)
      db.commit()
      db.refresh(storage)

    return storage

  @classmethod
  def create_builtin(
    cls,
    builtin_id: StorageID,
    type_: str,
    nickname: Opt[str] = None,
    config: Opt[dict] = None,
  ) -> StorageModel:
    """Create a built-in storage instance with explicit negative ID.

    :param builtin_id: Negative integer ID for the built-in storage
    :param type_: The storage type (class path)
    :param nickname: Optional descriptive nickname
    :param config: Optional configuration
    :return: The created storage model
    """
    if builtin_id >= 0:
      raise ValueError("Built-in storage IDs must be negative integers")

    with SessionLocal() as db:
      storage = StorageModel(
        id=builtin_id, type=type_, nickname=nickname, config=config or {}
      )
      db.add(storage)
      db.commit()
      db.refresh(storage)

    return storage

  @classmethod
  def setup_builtin_storages(cls) -> None:
    """Setup all built-in storage instances at application startup.

    Uses PostgreSQL upsert to ensure built-in storages exist with correct configuration.
    """
    builtin_storages = [
      {
        "id": -1,
        "type": "app.business.storage.http.HTTPImageStorage",
        "nickname": "http_image",
        "config": {},
      },
      {
        "id": -2,
        "type": "app.business.storage.http.HTTPVideoStorage",
        "nickname": "http_video",
        "config": {},
      },
      {
        "id": -3,
        "type": "app.business.storage.http.HTTPHtmlStorage",
        "nickname": "http_html",
        "config": {},
      },
    ]

    with SessionLocal() as db:
      for storage_data in builtin_storages:
        # Use PostgreSQL INSERT ... ON CONFLICT DO UPDATE
        stmt = sqlalchemy.dialects.postgresql.insert(StorageModel).values(
          id=storage_data["id"],
          type=storage_data["type"],
          nickname=storage_data["nickname"],
          config=storage_data["config"],
        )
        stmt = stmt.on_conflict_do_update(
          index_elements=["id"],
          set_=dict(
            type=stmt.excluded.type,
            nickname=stmt.excluded.nickname,
            config=stmt.excluded.config,
          ),
        )
        db.exec(stmt)  # type: ignore
      db.commit()


class Storage(abc.ABC, typing.Generic[ConfigTV]):
  """Storage base.

  Storage stores the actual content of a block.

  When block storage is None, initialize this base class.
  """

  __configschema__: dict
  """Storage configuration JSON schema"""
  __configcls__: type[ConfigTV]

  def __init_subclass__(
    cls, config_cls: type[sqlmodel.SQLModel] = _EmptyConfig, **kwargs
  ) -> None:
    cls.__configcls__ = config_cls  # type: ignore
    cls.__configschema__ = config_cls.model_json_schema()
    StorageManager.add_storage_type(cls)
    StorageManager.register_storage(cls)
    return super().__init_subclass__(**kwargs)

  def __init__(self, storage_record: Opt[StorageModel]):
    self._storage_record = storage_record
    if storage_record is not None:
      self._storage_id = storage_record.id
      self._storage_type = storage_record.type
      self._storage_nickname = storage_record.nickname
      self._storage_config = storage_record.config
    else:
      self._storage_id = None
      self._storage_type = None
      self._storage_nickname = None
      self._storage_config = {}

  def get_config(self) -> ConfigTV:
    """Get the configuration of the storage."""
    if self._storage_record is None:
      raise ValueError("No storage record available for inline content storage.")
    return typing.cast(ConfigTV, self.__configcls__.model_validate(self._storage_config))

  async def get_content(self, block: BlockModel) -> typing.Any:
    """Get the actual content of the block."""
    if self._storage_record is None:
      # Inline content storage
      return block.content
    else:
      raise NotImplementedError("Storage record is not None, should use concrete Storage.")
