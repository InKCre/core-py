"""OCI command and immutable extension profile tests."""

import pytest

from app.business.extension import ExtensionHost
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


def test_database_command_forwards_only_structured_arguments(monkeypatch):
  forwarded = {}
  import scripts.database

  monkeypatch.setattr(
    scripts.database,
    "main",
    lambda arguments: forwarded.update(arguments=arguments) or 0,
  )

  assert container._database(["migrate"]) == 0
  assert forwarded == {"arguments": ["migrate"]}


def test_host_exposes_no_legacy_target_or_catalog_manager():
  assert not hasattr(ExtensionHost, "download")
  assert not hasattr(ExtensionHost, "sync")


def test_dockerfile_contains_no_checked_in_extension_or_custom_bundle():
  dockerfile = (container.PROJECT_ROOT / "Dockerfile").read_text()

  assert "COPY extensions" not in dockerfile
  assert "extension-target" not in dockerfile
