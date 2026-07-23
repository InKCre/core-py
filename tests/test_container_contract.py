"""OCI command and immutable extension profile tests."""

import pytest

from app.business.extension import ExtensionManager
from scripts import container


def test_web_command_honors_platform_port(monkeypatch):
  executed = {}
  monkeypatch.setenv("PORT", "18080")
  monkeypatch.setattr(
    container.os,
    "execvp",
    lambda executable, arguments: executed.update(
      executable=executable,
      arguments=arguments,
    ),
  )

  assert container._web() == 0
  assert executed == {
    "executable": "uvicorn",
    "arguments": [
      "uvicorn",
      "run:api_app",
      "--host",
      "0.0.0.0",
      "--port",
      "18080",
    ],
  }


def test_web_command_rejects_invalid_port(monkeypatch):
  monkeypatch.setenv("PORT", "not-a-port")

  with pytest.raises(SystemExit, match="PORT must be an integer"):
    container._web()


def test_migrate_command_is_upgrade_only(monkeypatch):
  executed = {}
  monkeypatch.setattr(
    container.os,
    "execvp",
    lambda executable, arguments: executed.update(
      executable=executable,
      arguments=arguments,
    ),
  )

  assert container._migrate() == 0
  assert executed == {
    "executable": "alembic",
    "arguments": ["alembic", "upgrade", "head"],
  }


def test_release_artifact_has_no_runtime_extension_downloader():
  assert not hasattr(ExtensionManager, "download")


def test_install_rejects_extension_absent_from_artifact():
  with pytest.raises(ValueError, match="not part of this artifact"):
    ExtensionManager.install("not_checked_in")
