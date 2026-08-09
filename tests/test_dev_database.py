"""Tests for development runtime ownership and instance provenance."""

from pathlib import Path

import pytest

from scripts import dev_database


def _state(instance: str) -> dict:
  return {
    "format": 1,
    "identity": instance,
    "owner_repository": "InKCre/core-py",
    "project": f"inkcre-core-py-{instance}",
    "provider": {
      "kind": "ssh",
      "target": "docker-host",
      "docker_bin": "docker",
      "forward_host": "127.0.0.1",
    },
    "docker": {
      "kind": "ssh",
      "target": "docker-host",
      "engine": "28.5.2",
      "compose": "2.40.3",
      "daemon_id": "daemon-id",
      "daemon_name": "docker-desktop",
    },
    "contract_revision": "peer-database-runtime-v1",
    "migration_head": "f2a6c8e4b1d7",
    "source_revision": "a" * 40,
    "source_fingerprint": "b" * 64,
    "core_image": "inkcre-core-py-development:aaaaaaaaaaaa",
    "profile": "development",
    "local_ports": {"postgres": 51001, "core": 51002, "postgrest": 51003},
    "remote_ports": {"postgres": 61001, "core": 61002, "postgrest": 61003},
    "urls": {
      "core": "http://127.0.0.1:51002/",
      "postgrest": "http://127.0.0.1:51003/",
    },
    "tunnel": {"control_socket": "/tmp/inkcre-test-socket"},
  }


@pytest.mark.parametrize("instance", ("abc", "g" * 16, "a" * 17, "a;touch-file"))
def test_instance_requires_exact_svc_worktree_identity(instance):
  with pytest.raises(ValueError, match="SVC worktree instance"):
    dev_database._validate_instance(instance)


def test_compose_project_is_repository_qualified():
  instance = "0123456789abcdef"

  assert dev_database._project_name(instance) == ("inkcre-core-py-0123456789abcdef")


def test_runtime_profile_carries_cross_peer_instance_provenance(
  monkeypatch,
  tmp_path,
):
  instance = "0123456789abcdef"
  runtime_directory = tmp_path / instance
  monkeypatch.setattr(
    dev_database,
    "_runtime_directory",
    lambda selected: runtime_directory
    if selected == instance
    else Path("/unexpected-runtime"),
  )
  credentials = {
    "format": 1,
    "JWT_SECRET": "jwt-secret",
    "POSTGRES_PASSWORD": "postgres-secret",
    "CORE_DATABASE_PASSWORD": "core-secret",
    "POSTGREST_DATABASE_PASSWORD": "postgrest-secret",
  }

  dev_database._write_runtime_files(_state(instance), credentials)

  profile = dev_database._read_json(runtime_directory / "profile.json")
  profile_text = (runtime_directory / "profile.json").read_text()
  assert profile["runtime"] == {
    "compose_project": "inkcre-core-py-0123456789abcdef",
    "docker_daemon_id": "daemon-id",
    "instance": instance,
    "owner_repository": "InKCre/core-py",
    "source_fingerprint": "b" * 64,
    "source_revision": "a" * 40,
  }
  assert profile["database_contract"]["revision"] == "peer-database-runtime-v1"
  assert profile["jwt"]["audience"] == "inkcre-api"
  assert "jwt-secret" not in profile_text
  assert "postgres-secret" not in profile_text
  assert (runtime_directory / "credential.json").stat().st_mode & 0o777 == 0o600


def test_runtime_state_rejects_another_repository_owner(monkeypatch, tmp_path):
  instance = "0123456789abcdef"
  runtime_directory = tmp_path / instance
  runtime_directory.mkdir()
  state = _state(instance)
  state["owner_repository"] = "InKCre/client-web"
  (runtime_directory / "runtime.json").write_text(dev_database._stable_json(state))
  monkeypatch.setattr(
    dev_database,
    "_runtime_directory",
    lambda selected: runtime_directory,
  )

  with pytest.raises(ValueError, match="another repository"):
    dev_database._read_state(instance)


def test_source_fingerprint_names_and_hashes_each_file(monkeypatch, tmp_path):
  compose = tmp_path / "docker-compose.yml"
  first = tmp_path / "first"
  second = tmp_path / "second"
  compose.write_text("services: {}")
  first.write_text("same")
  second.write_text("same")
  monkeypatch.setattr(
    dev_database,
    "PROJECT_ROOT",
    tmp_path,
  )
  monkeypatch.setattr(
    dev_database,
    "iter_build_context_files",
    lambda: iter((first, second)),
  )
  initial = dev_database._source_fingerprint()

  compose.write_text("services:\n  postgres: {}")

  assert dev_database._source_fingerprint() != initial
