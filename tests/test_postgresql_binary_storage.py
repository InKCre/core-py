"""Caller-session contract for deployment-owned PostgreSQL raw bytes."""

import uuid

from app.business.info_base.storage.postgresql import (
  PostgreSQLBinaryStorage,
  StorageBlobNotFoundError,
)
from app.schemas.info_base.storage import StorageBlobModel, StorageModel
import pytest


class _BlobSession:
  def __init__(self):
    self.blobs: dict[uuid.UUID, StorageBlobModel] = {}

  def add(self, blob):
    self.blobs[blob.id] = blob

  def flush(self):
    return None

  def refresh(self, _blob):
    return None

  def get(self, model, blob_id):
    assert model is StorageBlobModel
    return self.blobs.get(blob_id)

  def delete(self, blob):
    del self.blobs[blob.id]


def _storage() -> PostgreSQLBinaryStorage:
  return PostgreSQLBinaryStorage(
    StorageModel(
      id=-4,
      type="postgresql_binary",
      nickname="PostgreSQL Binary",
      config={},
    )
  )


def test_write_read_delete_share_the_callers_transaction():
  session = _BlobSession()
  storage = _storage()

  blob_id = storage.write_raw_content(b"raw-bytes", session)  # type: ignore[arg-type]
  pointer = '{"blob_id":"%s","resolver_metadata":"ignored"}' % blob_id

  assert storage.read_raw_content(pointer, session) == b"raw-bytes"  # type: ignore[arg-type]
  assert storage.delete_raw_content(pointer, session) is True  # type: ignore[arg-type]
  with pytest.raises(StorageBlobNotFoundError):
    storage.read_raw_content(pointer, session)  # type: ignore[arg-type]


def test_delete_of_an_already_missing_blob_is_false():
  session = _BlobSession()
  pointer = '{"blob_id":"00000000-0000-0000-0000-000000000017"}'

  assert _storage().delete_raw_content(pointer, session) is False  # type: ignore[arg-type]
