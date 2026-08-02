"""Health and readiness contract tests."""

from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.database_contract import readiness
from app.database_contract.readiness import ContractReadiness
from app.runtime import RUNTIME_STATUS, RuntimePhase
import run


def _ready_contract() -> ContractReadiness:
  return ContractReadiness(
    profile="runtime",
    components={
      "database": {"status": "ok", "environment": "runtime"},
      "migration": {
        "status": "ok",
        "current": ["head"],
        "expected": ["head"],
      },
      "roles": {"status": "ok", "problems": []},
      "privileges": {"status": "ok", "problems": []},
      "catalog": {"status": "ok", "problems": []},
      "seed": {"status": "not_required"},
    },
  )


def test_contract_readiness_reports_first_failed_component():
  result = ContractReadiness(
    profile="runtime",
    components={
      "database": {"status": "ok"},
      "migration": {"status": "error"},
    },
  )

  assert result.ready is False
  assert result.reason == "migration_mismatch"
  assert result.as_dict()["status"] == "error"


def test_database_readiness_sanitizes_connection_failures(monkeypatch):
  @contextmanager
  def broken_connection(_database_url=None):
    raise RuntimeError("secret-bearing driver error")
    yield

  monkeypatch.setattr(readiness, "database_connection", broken_connection)

  result = readiness.check_database_contract(
    database_url="postgresql+psycopg://user:secret@example/test"
  )

  assert result.ready is False
  assert result.reason == "database_mismatch"
  assert "secret" not in str(result.as_dict())


def test_liveness_is_process_only_and_requires_no_jwt():
  response = TestClient(run.api_app).get("/livez")

  assert response.status_code == 200
  assert response.json() == {"status": "ok"}


def test_readiness_requires_database_and_runtime(monkeypatch):
  original_phase = RUNTIME_STATUS.phase
  original_reason = RUNTIME_STATUS.reason
  monkeypatch.setattr(run, "check_database_readiness", _ready_contract)
  RUNTIME_STATUS.set(RuntimePhase.READY, "ready")

  try:
    response = TestClient(run.api_app).get("/readyz")
  finally:
    RUNTIME_STATUS.set(original_phase, original_reason)

  assert response.status_code == 200
  assert response.json()["status"] == "ready"
