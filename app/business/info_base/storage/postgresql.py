"""Writable PostgreSQL binary storage."""

import uuid

import pydantic
import sqlmodel

from app.schemas.info_base.storage import StorageBlobModel
from .main import WritableStorage


class PostgreSQLBinaryStorageConfig(sqlmodel.SQLModel):
  pass


class PostgreSQLBlobPointer(pydantic.BaseModel):
  """Minimum pointer fields accepted from storage-backed block content."""

  model_config = pydantic.ConfigDict(extra="ignore")

  blob_id: uuid.UUID


class StorageBlobNotFoundError(LookupError):
  pass


class PostgreSQLBinaryStorage(
  WritableStorage[PostgreSQLBinaryStorageConfig, bytes],
  stg_type="postgresql_binary",
  config_cls=PostgreSQLBinaryStorageConfig,
):
  """Store raw bytes in the protocol database and return an opaque UUID pointer."""

  def serialize_pointer(self, pointer: object) -> str:
    blob_id = pydantic.TypeAdapter(uuid.UUID).validate_python(pointer)
    return PostgreSQLBlobPointer(blob_id=blob_id).model_dump_json()

  def read_raw_content(
    self,
    block_content: str,
    db_session: sqlmodel.Session,
  ) -> bytes:
    pointer = PostgreSQLBlobPointer.model_validate_json(block_content)
    blob = db_session.get(StorageBlobModel, pointer.blob_id)
    if blob is None:
      raise StorageBlobNotFoundError(f"Storage blob {pointer.blob_id} not found")
    return blob.data

  def write_raw_content(
    self,
    content: bytes,
    db_session: sqlmodel.Session,
  ) -> uuid.UUID:
    blob = StorageBlobModel(data=content)
    db_session.add(blob)
    db_session.flush()
    db_session.refresh(blob)
    return blob.id

  def update_raw_content(
    self,
    block_content: str,
    content: bytes,
    db_session: sqlmodel.Session,
  ) -> bool:
    pointer = PostgreSQLBlobPointer.model_validate_json(block_content)
    blob = db_session.get(StorageBlobModel, pointer.blob_id)
    if blob is None:
      return False
    blob.data = content
    db_session.add(blob)
    db_session.flush()
    return True

  def delete_raw_content(
    self,
    block_content: str,
    db_session: sqlmodel.Session,
  ) -> bool:
    pointer = PostgreSQLBlobPointer.model_validate_json(block_content)
    blob = db_session.get(StorageBlobModel, pointer.blob_id)
    if blob is None:
      return False
    db_session.delete(blob)
    db_session.flush()
    return True
