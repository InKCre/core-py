"""Block-owned hydration and instance snapshot behavior."""

import asyncio

from app.business.info_base.storage import StorageManager
from app.schemas.info_base.block import BlockModel
import pytest


class _Storage:
  def __init__(self, values: list[object]):
    self.values = values
    self.calls = 0

  async def get_raw_content(self, _pointer: str):
    value = self.values[self.calls]
    self.calls += 1
    return value


def _install_storage(monkeypatch: pytest.MonkeyPatch, storage: _Storage) -> None:
  monkeypatch.setattr(
    StorageManager,
    "get_storage",
    classmethod(lambda _cls, _storage_id: storage),
  )


def test_inline_content_is_the_hydrated_value():
  block = BlockModel(resolver="core.text.v1", content="authored", storage=None)

  assert asyncio.run(block.get_hydrated_content()) == "authored"


def test_storage_hydration_is_cached_per_block_instance_and_refreshable(monkeypatch):
  storage = _Storage([b"first", b"second"])
  _install_storage(monkeypatch, storage)
  block = BlockModel(
    resolver="core.file.v1",
    content='{"blob_id":"00000000-0000-0000-0000-000000000001"}',
    storage=-4,
  )

  assert asyncio.run(block.get_hydrated_content()) == b"first"
  assert asyncio.run(block.get_hydrated_content()) == b"first"
  assert storage.calls == 1
  assert asyncio.run(block.get_hydrated_content(refresh=True)) == b"second"
  assert storage.calls == 2


def test_changed_pointer_misses_the_instance_cache(monkeypatch):
  storage = _Storage([b"first", b"second"])
  _install_storage(monkeypatch, storage)
  block = BlockModel(resolver="core.file.v1", content="pointer-one", storage=-4)

  assert asyncio.run(block.get_hydrated_content()) == b"first"
  block.content = "pointer-two"
  assert asyncio.run(block.get_hydrated_content()) == b"second"


def test_configured_storage_must_return_bytes(monkeypatch):
  storage = _Storage(["decoded by storage"])
  _install_storage(monkeypatch, storage)
  block = BlockModel(resolver="core.text.v1", content="pointer", storage=-4)

  with pytest.raises(TypeError, match="configured storage must return bytes"):
    asyncio.run(block.get_hydrated_content())


def test_orm_loaded_instance_lazily_initializes_private_cache_state(monkeypatch):
  storage = _Storage([b"loaded"])
  _install_storage(monkeypatch, storage)
  block = BlockModel(resolver="core.file.v1", content="pointer", storage=-4)
  object.__setattr__(block, "__pydantic_private__", None)

  assert asyncio.run(block.get_hydrated_content()) == b"loaded"
  assert asyncio.run(block.get_hydrated_content()) == b"loaded"
  assert storage.calls == 1
