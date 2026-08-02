"""Tests for the provider-neutral development Docker transport."""

from io import BytesIO
from pathlib import Path
import subprocess
import tarfile

import pytest

from scripts import dev_database_provider as provider


def test_local_provider_is_the_portable_environment_default(monkeypatch):
  monkeypatch.setenv("INKCRE_DATABASE_PROVIDER", "local")

  assert provider.resolve_database_provider() == provider.DatabaseProvider(kind="local")


def test_ssh_provider_uses_only_validated_machine_values(monkeypatch):
  monkeypatch.setenv("INKCRE_DATABASE_PROVIDER", "ssh")
  monkeypatch.setenv("INKCRE_DATABASE_SSH_TARGET", "wsl.win-ws.localhost")
  monkeypatch.setenv("INKCRE_DATABASE_SSH_DOCKER_BIN", "/opt/docker client")

  resolved = provider.resolve_database_provider()

  assert resolved.kind == "ssh"
  assert resolved.target == "wsl.win-ws.localhost"
  assert resolved.docker_bin == "/opt/docker client"
  assert resolved.forward_host == "127.0.0.1"


@pytest.mark.parametrize(
  "target",
  ("host;uname", "host name", "-host", "host\nname"),
)
def test_ssh_provider_rejects_option_and_shell_injection(monkeypatch, target):
  monkeypatch.setenv("INKCRE_DATABASE_PROVIDER", "ssh")
  monkeypatch.setenv("INKCRE_DATABASE_SSH_TARGET", target)

  with pytest.raises(ValueError, match="SSH-config host alias"):
    provider.resolve_database_provider()


def test_environment_quoting_is_single_line():
  assert provider.quote_environment_value("a'b") == "'a'\\''b'"

  with pytest.raises(ValueError, match="one non-empty line"):
    provider.quote_environment_value("a\nb")


def test_remote_payload_contains_only_the_runtime_build_surface(tmp_path):
  environment = tmp_path / "compose.env"
  environment.write_text("INKCRE_COMPOSE_PROJECT_NAME='test'\n")

  payload = provider._remote_payload(environment, ("config", "--quiet"))

  with tarfile.open(fileobj=BytesIO(payload)) as archive:
    names = set(archive.getnames())

  assert "database.compose.yml" in names
  assert "remote-compose.sh" in names
  assert "compose.args" in names
  assert "context/Dockerfile" in names
  assert "context/app" in names
  assert "context/tasks" not in names
  assert "context/.env" not in names
  assert not any("__pycache__" in Path(name).parts for name in names)


def test_provider_equality_includes_exact_ssh_target_and_binary():
  first = provider.DatabaseProvider(
    kind="ssh",
    target="docker-a",
    docker_bin="docker",
    forward_host="127.0.0.1",
  )
  second = provider.DatabaseProvider(
    kind="ssh",
    target="docker-b",
    docker_bin="docker",
    forward_host="127.0.0.1",
  )

  assert provider.same_database_provider(first, first)
  assert not provider.same_database_provider(first, second)


def test_compose_failure_is_actionable_and_redacts_runtime_secrets(
  monkeypatch,
  tmp_path,
):
  environment = tmp_path / "compose.env"
  environment.write_text(
    "JWT_SECRET='development-secret-value'\nINKCRE_COMPOSE_PROJECT_NAME='test'\n"
  )

  def fail(*_args, **_kwargs):
    raise subprocess.CalledProcessError(
      17,
      ["docker", "compose"],
      stderr=b"remote failure for development-secret-value",
    )

  monkeypatch.setattr(provider, "_run", fail)

  with pytest.raises(
    RuntimeError,
    match=r"local Docker Compose failed with exit 17: remote failure for \[REDACTED\]",
  ):
    provider.run_database_compose(
      provider.DatabaseProvider(kind="local"),
      "inkcre-test",
      environment,
      ("up",),
    )
