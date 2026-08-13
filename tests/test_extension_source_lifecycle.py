"""Extension-owned Source publication over the global Job architecture."""

import sqlmodel
import pydantic

import app.business.source.main as source_module
from app.business.source.main import SourceBase, SourceManager
from app.schemas.job import JobModel


class SourceConfig(sqlmodel.SQLModel):
  pass


def make_source_class():
  class ExtensionSource(SourceBase[SourceConfig], config_cls=SourceConfig):
    async def collect(self, job: JobModel, config: pydantic.BaseModel) -> None:
      del job, config

  transient_key = f"{ExtensionSource.__module__}.{ExtensionSource.__qualname__}"
  SourceManager._SOURCE_CLASSES.pop(transient_key)
  ExtensionSource.__module__ = "extensions.fixture.source"
  ExtensionSource.__qualname__ = "Source"
  return ExtensionSource


def test_sync_source_types_persists_only_the_selected_publication(monkeypatch):
  source_class = make_source_class()
  source_type = "extensions.fixture.source.Source"
  statements: list[dict[str, object]] = []

  class FakeSession:
    def __enter__(self):
      return self

    def __exit__(self, *args):
      return None

    def exec(self, statement):
      statements.append(statement.compile().params)

    def commit(self):
      return None

  monkeypatch.setattr(source_module, "SessionLocal", FakeSession)
  SourceManager.sync_source_types({source_type: source_class})

  assert [statement["id"] for statement in statements] == [source_type]


def test_registry_restore_removes_only_the_exact_extension_publication():
  source_class = make_source_class()
  source_type = "extensions.fixture.source.Source"
  before = SourceManager.snapshot_source_types()
  try:
    SourceManager.add_source_type(source_class)
    published = SourceManager.snapshot_source_types()
    SourceManager.restore_source_types(before, published)
    assert not SourceManager.has_source_type(source_type)
  finally:
    SourceManager._SOURCE_CLASSES = before
