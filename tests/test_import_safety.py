"""Regression tests for import-safe registries and application construction."""

import os
from pathlib import Path
import subprocess
import sys
import typing


from app.business.info_base.storage import main as storage_module
from app.business.source import main as source_module


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def fail_session():
  raise AssertionError("registry import attempted to open a database session")


def test_storage_registration_is_memory_only(monkeypatch):
  class TestStorage:
    __stgtype__ = "test.import_safe"
    __doc__ = "test"
    __configschema__ = {}

  monkeypatch.setattr(storage_module, "SessionLocal", fail_session)
  try:
    storage_class = typing.cast(type[storage_module.Storage], TestStorage)
    storage_module.StorageManager.register_storage(storage_class)
    assert (
      storage_module.StorageManager._STORAGE_CLASSES[TestStorage.__stgtype__] is TestStorage
    )
  finally:
    storage_module.StorageManager._STORAGE_CLASSES.pop(
      TestStorage.__stgtype__,
      None,
    )


def test_source_registration_is_memory_only(monkeypatch):
  class TestSource:
    __module__ = "tests.import_safe"
    __qualname__ = "TestSource"
    __doc__ = "test"
    __configschema__ = {}

  source_type = f"{TestSource.__module__}.{TestSource.__qualname__}"
  monkeypatch.setattr(source_module, "SessionLocal", fail_session)
  try:
    source_class = typing.cast(type[source_module.SourceBase], TestSource)
    source_module.SourceManager.add_source_type(source_class)
    assert source_module.SourceManager._SOURCE_CLASSES[source_type] is TestSource
  finally:
    source_module.SourceManager._SOURCE_CLASSES.pop(source_type, None)


def test_application_import_and_openapi_are_database_independent(tmp_path):
  environment = {
    **os.environ,
    "INKCRE_ENV_FILE": "",
    "DATABASE_URL": "postgresql+psycopg://test:test@127.0.0.1:1/test",
    "JWT_SECRET": "test-only-jwt-secret-at-least-32-bytes",
    "LLM_SP_AK": "",
    "LLM_SP_BASE_URL": "",
    "OBSRV__LOGGING_BACKEND": "none",
    "SKIP_EXTENSION_START": "1",
    "PYTHONPATH": str(PROJECT_ROOT),
  }
  result = subprocess.run(  # noqa: S603
    [
      sys.executable,
      "-c",
      (
        "from run import api_app; schema=api_app.openapi(); "
        "assert '/extensions/{namespace}/{name}' in schema['paths']; "
        "print(len(schema['paths']))"
      ),
    ],
    cwd=tmp_path,
    env=environment,
    check=False,
    capture_output=True,
    text=True,
    timeout=10,
  )

  assert result.returncode == 0, result.stderr
  assert int(result.stdout.strip().splitlines()[-1]) > 0
