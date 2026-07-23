"""Health and readiness contract tests."""

from collections.abc import Iterable

from fastapi.testclient import TestClient

from app import health
from app.health import DatabaseReadiness
from app.runtime import RUNTIME_STATUS, RuntimePhase
import run


class FakeScalarResult:
  def __init__(self, values: Iterable[str] = ()):
    self.values = tuple(values)

  def scalars(self) -> tuple[str, ...]:
    return self.values


class FakeConnection:
  def __init__(self, current_heads: Iterable[str]):
    self.current_heads = tuple(current_heads)

  def __enter__(self):
    return self

  def __exit__(self, *_args):
    return None

  def execute(self, statement):
    if "alembic_version" in str(statement):
      return FakeScalarResult(self.current_heads)
    return FakeScalarResult()


class FakeEngine:
  def __init__(self, current_heads: Iterable[str] = (), error: Exception | None = None):
    self.current_heads = tuple(current_heads)
    self.error = error
    self.disposed = False

  def connect(self):
    if self.error:
      raise self.error
    return FakeConnection(self.current_heads)

  def dispose(self):
    self.disposed = True


def test_database_readiness_accepts_exact_repository_heads(monkeypatch):
  expected = health.get_repository_heads()
  engine = FakeEngine(expected)
  monkeypatch.setattr(health, "create_engine", lambda *_args, **_kwargs: engine)

  result = health.check_database_readiness("postgresql+psycopg://example")

  assert result.ready is True
  assert result.reason == "ready"
  assert result.current_heads == expected
  assert engine.disposed is True


def test_database_readiness_rejects_migration_mismatch(monkeypatch):
  engine = FakeEngine(("obsolete",))
  monkeypatch.setattr(health, "create_engine", lambda *_args, **_kwargs: engine)

  result = health.check_database_readiness("postgresql+psycopg://example")

  assert result.ready is False
  assert result.reason == "migration_head_mismatch"
  assert result.current_heads == ("obsolete",)


def test_database_readiness_sanitizes_connection_failures(monkeypatch):
  engine = FakeEngine(error=RuntimeError("secret-bearing driver error"))
  monkeypatch.setattr(health, "create_engine", lambda *_args, **_kwargs: engine)

  result = health.check_database_readiness("postgresql+psycopg://user:secret@example")

  assert result.ready is False
  assert result.reason == "database_unreachable_or_migration_state_unavailable"
  assert "secret" not in str(result.as_dict())
  assert engine.disposed is True


def test_liveness_is_process_only_and_requires_no_jwt():
  response = TestClient(run.api_app).get("/livez")

  assert response.status_code == 200
  assert response.json() == {"status": "ok"}


def test_readiness_requires_database_and_runtime(monkeypatch):
  original_phase = RUNTIME_STATUS.phase
  original_reason = RUNTIME_STATUS.reason
  database = DatabaseReadiness(
    ready=True,
    reason="ready",
    expected_heads=("head",),
    current_heads=("head",),
  )
  monkeypatch.setattr(run, "check_database_readiness", lambda: database)
  RUNTIME_STATUS.set(RuntimePhase.READY, "ready")

  try:
    response = TestClient(run.api_app).get("/readyz")
  finally:
    RUNTIME_STATUS.set(original_phase, original_reason)

  assert response.status_code == 200
  assert response.json()["status"] == "ready"
