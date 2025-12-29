__all__ = [
  "StorageManager",
  "Storage",
]

import abc
import importlib
import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlmodel
import typing
from typing import Optional as Opt
from app.engine import SessionLocal
from app.schemas.info_base.storage import (
  StorageID,
  StorageTypeID,
  StorageModel,
  StorageTypesModel,
)


ConfigTV = typing.TypeVar("ConfigTV", bound=sqlmodel.SQLModel)
ContentTV = typing.TypeVar("ContentTV")


class _EmptyConfig(sqlmodel.SQLModel):
  """Default empty config class for storages without configuration."""


class StorageManager:
  _STORAGE_CLASSES: dict[StorageTypeID, type["Storage"]] = {}
  """Storage type registry: type ID -> Storage class"""

  @classmethod
  def register_storage(cls, storage_cls: type["Storage"]):
    """Register a storage class."""
    cls._STORAGE_CLASSES[storage_cls.__stgtype__] = storage_cls

    stmt = sqlalchemy.dialects.postgresql.insert(StorageTypesModel).values(
      id=storage_cls.__stgtype__,
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
  def get_storage(cls, storage_id: StorageID) -> "Storage":
    """Create a storage instance."""
    with SessionLocal() as db:
      storage_record = db.exec(
        sqlmodel.select(StorageModel).where(StorageModel.id == storage_id)
      ).one()
    storage_class = cls._STORAGE_CLASSES.get(storage_record.type)
    if storage_class is None:
      # Dynamically import the storage class
      module_path, class_name = storage_record.type.rsplit(".", 1)
      module = importlib.import_module(module_path)
      storage_class = getattr(module, class_name)

    return storage_class(storage_record)

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
    :param type_: The storage type
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
        "type": "http_image",
        "nickname": "HTTP Image",
        "config": {},
      },
      {
        "id": -2,
        "type": "http_video",
        "nickname": "HTTP Video",
        "config": {},
      },
      {
        "id": -3,
        "type": "http_html",
        "nickname": "HTTP HTML",
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


class Storage(abc.ABC, typing.Generic[ConfigTV, ContentTV]):
  """Storage base.
  Storage retrieves the raw content from block record.

  Generic parameters:
    - ConfigTV: Configuration type variable
    - ContentTV: Content type variable
  """

  __configschema__: dict
  """Storage configuration JSON schema"""
  __configcls__: type[ConfigTV]
  __stgtype__: StorageTypeID
  """Storage type identifier"""

  def __init_subclass__(
    cls, stg_type: StorageTypeID, config_cls: type[ConfigTV] = _EmptyConfig, **kwargs
  ) -> None:
    """
    :param stg_type: Unique storage type string
    :param config_cls: Configuration class for the storage
    """
    cls.__configcls__ = config_cls
    cls.__configschema__ = config_cls.model_json_schema()
    cls.__stgtype__ = stg_type
    StorageManager.register_storage(cls)
    return super().__init_subclass__(**kwargs)

  def __init__(self, storage_record: StorageModel):
    self._config = self.__configcls__.model_validate(storage_record.config)

    self.__post_init__()

  def __post_init__(self):
    """Post-initialization hook for subclasses."""
    pass

  async def get_raw_content(self, block_content: str) -> ContentTV:
    """Get the raw content of the block."""
    raise NotImplementedError(
      f"{self.__class__.__name__}.get_raw_content() must be implemented by subclasses."
    )
