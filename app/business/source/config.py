"""Deployment-wide policy used by Source-owned content materialization."""

import typing

import pydantic

from app.business.deployment_config import DeploymentConfigManager
from app.business.info_base.storage import StorageManager, WritableStorage
from app.schemas.info_base.storage import StorageID
from app.schemas.source import SourceModel
from app.persistence.source.uow import SourceUnitOfWork
import sqlmodel


SOURCE_CONFIG_KEY = "core.source"
SOURCE_CONFIG_SCHEMA_ID = "core.source.config.v1"
POSTGRESQL_BINARY_STORAGE_ID = -4


class SourceDeploymentConfig(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid")

  default_storage: StorageID = POSTGRESQL_BINARY_STORAGE_ID


DeploymentConfigManager.register_schema(
  SOURCE_CONFIG_SCHEMA_ID, SourceDeploymentConfig, keys=(SOURCE_CONFIG_KEY,)
)


def resolve_writable_storage(
  source: SourceModel,
  db_session: sqlmodel.Session,
) -> WritableStorage:
  """Resolve Source override → deployment default → built-in PostgreSQL binary."""
  storage_id = source.storage
  if storage_id is None:
    persisted = DeploymentConfigManager.get(SOURCE_CONFIG_KEY)
    storage_id = (
      POSTGRESQL_BINARY_STORAGE_ID
      if persisted is None
      else typing.cast(SourceDeploymentConfig, persisted).default_storage
    )
  storage = StorageManager.get_storage(storage_id, db_session)
  if not isinstance(storage, WritableStorage):
    raise ValueError(f"Storage {storage_id} is not writable")
  return storage


async def resolve_writable_storage_async(
  source: SourceModel, uow: SourceUnitOfWork
) -> WritableStorage:
  """Resolve storage using the caller's Source/graph/config transaction."""
  storage_id = source.storage
  if storage_id is None:
    record = await uow.configuration.get(SOURCE_CONFIG_KEY)
    persisted = None if record is None else DeploymentConfigManager._restore_record(record)
    storage_id = (
      POSTGRESQL_BINARY_STORAGE_ID
      if persisted is None
      else typing.cast(SourceDeploymentConfig, persisted).default_storage
    )
  storage = StorageManager.from_record(await uow.graph.storage.get(storage_id))
  if not isinstance(storage, WritableStorage):
    raise ValueError(f"Storage {storage_id} is not writable")
  return storage
