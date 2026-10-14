import json
from contextlib import nullcontext
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import time
import uuid

import psycopg
import pytest

from scripts.automation.production_preflight import (
  checked_in_production_profile,
  collect_database_inventory,
  quiescence_conflicts,
  read_flush_lsn,
  verify_app_configuration,
)


CORE_APP_NAME = "inkcre-core-production"
CORE_PEER_ID = uuid.uuid5(uuid.NAMESPACE_URL, CORE_APP_NAME)


class SnapshotCursor:
  def __init__(self, *, v2: bool) -> None:
    self.v2 = v2
    self.statement = ""
    self.parameters = ()
    self.statements: list[str] = []

  def execute(self, statement: str, parameters=()) -> None:
    self.statement = statement
    self.parameters = parameters
    self.statements.append(statement)

  def fetchall(self):
    if "version_num" in self.statement:
      return [("3d9593b0c855",)]
    if "contract_revision" in self.statement:
      return [("peer-extension-setup-v1", "production", "neondb_owner")]
    if "FROM inkcre.peers" in self.statement:
      return [(str(CORE_PEER_ID), "core-py", "0.7.1", None, False)]
    if "to_regclass" in self.statement:
      return [(self.v2,)]
    if "FROM inkcre.extension_peer_participations" in self.statement:
      return [("inkcre/mail", str(CORE_PEER_ID), "python", "0.3.2", True)]
    if "FROM inkcre.extensions" in self.statement:
      return [("inkcre/mail", str(CORE_PEER_ID), None, "0.3.2", True)]
    if "FROM inkcre.jobs" in self.statement:
      return [(42, "core.source.collect.v1", "running", None, None, False)]
    if "FROM pg_auth_members" in self.statement:
      return [("inkcre_core", "authenticated", False)]
    if "FROM pg_roles AS role" in self.statement:
      return [("inkcre_core", "peers", True, True, False, False, False)]
    if "FROM pg_roles" in self.statement:
      return [("inkcre_core", True, True, False, False, False, False, False)]
    if "FROM pg_stat_activity" in self.statement:
      return [("inkcre_core", "core-py", "client backend", "active", None)]
    raise AssertionError(f"unexpected query: {self.statement}")


class SnapshotConnection:
  def __init__(self, *, v2: bool) -> None:
    self.fake_cursor = SnapshotCursor(v2=v2)

  def transaction(self):
    return nullcontext()

  def cursor(self):
    return self.fake_cursor


@pytest.mark.parametrize(
  ("v2", "expected_source", "expected_distribution"),
  [(True, "peer_participations", "python"), (False, "legacy_extension_snapshot", None)],
)
def test_database_inventory_is_read_only_and_distinguishes_legacy_pins(
  v2: bool, expected_source: str, expected_distribution: str | None
) -> None:
  connection = SnapshotConnection(v2=v2)

  inventory = collect_database_inventory(connection, CORE_PEER_ID)

  assert inventory["extension_selection_source"] == expected_source
  assert inventory["extension_selections"][0]["distribution"] == expected_distribution
  assert inventory["extension_selections"][0]["version"] == "0.3.2"
  assert inventory["active_jobs"][0]["id"] == 42
  assert all(
    statement.lstrip().upper().startswith(("SELECT", "SET TRANSACTION"))
    for statement in connection.fake_cursor.statements
  )
  assert "does not prove" in inventory["observation_limit"]


def test_quiescence_gate_rejects_observed_peers_jobs_and_sessions() -> None:
  inventory = {
    "peers": [
      {"id": str(CORE_PEER_ID), "lease_active": True},
      {"id": str(uuid.uuid4()), "lease_active": True},
    ],
    "active_jobs": [{"status": "running"}],
    "database_sessions": [{"user": "authenticator"}],
  }

  assert quiescence_conflicts(inventory, CORE_PEER_ID) == [
    "another Peer still has an active database lease",
    "a database Job is still running",
    "database sessions remain after the configured apps were stopped",
  ]


def test_quiescence_gate_allows_only_core_lease_and_pending_jobs() -> None:
  inventory = {
    "peers": [{"id": str(CORE_PEER_ID), "lease_active": True}],
    "active_jobs": [{"status": "pending"}],
    "database_sessions": [],
  }

  assert quiescence_conflicts(inventory, CORE_PEER_ID) == []


def test_quiescence_gate_allows_idle_client_backends_without_transactions() -> None:
  inventory = {
    "peers": [{"id": str(CORE_PEER_ID), "lease_active": True}],
    "active_jobs": [{"status": "pending"}],
    "database_sessions": [
      {
        "user": "inkcre_core",
        "application": "pgbouncer",
        "backend_type": "client backend",
        "state": "idle",
        "transaction_started_at": None,
      },
    ],
  }

  assert quiescence_conflicts(inventory, CORE_PEER_ID) == []


@pytest.mark.parametrize(
  "session",
  [
    {
      "backend_type": "client backend",
      "state": "active",
      "transaction_started_at": None,
    },
    {
      "backend_type": "client backend",
      "state": "idle in transaction",
      "transaction_started_at": "2026-10-14T05:00:00Z",
    },
    {
      "backend_type": "client backend",
      "state": "idle in transaction (aborted)",
      "transaction_started_at": "2026-10-14T05:00:00Z",
    },
    {
      "backend_type": "client backend",
      "state": "idle",
      "transaction_started_at": "2026-10-14T05:00:00Z",
    },
    {
      "backend_type": "background worker",
      "state": "idle",
      "transaction_started_at": None,
    },
    {"state": "disabled"},
  ],
)
def test_quiescence_gate_rejects_non_idle_or_unknown_database_sessions(
  session: dict,
) -> None:
  inventory = {
    "peers": [{"id": str(CORE_PEER_ID), "lease_active": True}],
    "active_jobs": [],
    "database_sessions": [session],
  }

  assert quiescence_conflicts(inventory, CORE_PEER_ID) == [
    "database sessions remain after the configured apps were stopped",
  ]


def test_quiescence_gate_tracks_real_postgresql_session_states() -> None:
  database_url = os.environ.get("PRODUCTION_PREFLIGHT_TEST_DATABASE_URL")
  if not database_url:
    pytest.skip("a disposable PostgreSQL URL is not configured")

  inventory = {
    "peers": [{"id": str(CORE_PEER_ID), "lease_active": True}],
    "active_jobs": [],
    "database_sessions": [],
  }
  with (
    psycopg.connect(database_url, autocommit=True) as subject,
    psycopg.connect(database_url, autocommit=True) as observer,
  ):
    subject_pid = subject.info.backend_pid

    def observe_subject() -> dict:
      row = observer.execute(
        """
        SELECT backend_type, state, xact_start
        FROM pg_stat_activity
        WHERE pid = %s
        """,
        (subject_pid,),
      ).fetchone()
      assert row is not None
      return {
        "backend_type": row[0],
        "state": row[1],
        "transaction_started_at": row[2],
      }

    inventory["database_sessions"] = [observe_subject()]
    assert quiescence_conflicts(inventory, CORE_PEER_ID) == []

    subject.execute("BEGIN")
    inventory["database_sessions"] = [observe_subject()]
    assert inventory["database_sessions"][0]["state"] == "idle in transaction"
    assert inventory["database_sessions"][0]["transaction_started_at"] is not None
    assert quiescence_conflicts(inventory, CORE_PEER_ID) == [
      "database sessions remain after the configured apps were stopped",
    ]
    subject.execute("ROLLBACK")

    with ThreadPoolExecutor(max_workers=1) as executor:
      query = executor.submit(subject.execute, "SELECT pg_sleep(2)")
      deadline = time.monotonic() + 5
      while time.monotonic() < deadline:
        session = observe_subject()
        if session["state"] == "active":
          inventory["database_sessions"] = [session]
          assert quiescence_conflicts(inventory, CORE_PEER_ID) == [
            "database sessions remain after the configured apps were stopped",
          ]
          break
        time.sleep(0.02)
      else:
        pytest.fail("could not observe the disposable PostgreSQL query as active")
      query.result(timeout=5)

    inventory["database_sessions"] = [observe_subject()]
    assert inventory["database_sessions"][0]["state"] == "idle"
    assert inventory["database_sessions"][0]["transaction_started_at"] is None
    assert quiescence_conflicts(inventory, CORE_PEER_ID) == []


def test_flush_lsn_is_read_only_and_validates_the_database_value() -> None:
  class LsnCursor:
    def __init__(self, value: str) -> None:
      self.value = value
      self.statements: list[str] = []

    def execute(self, statement: str) -> None:
      self.statements.append(statement)

    def fetchone(self):
      return (self.value,)

  class LsnConnection:
    def __init__(self, value: str) -> None:
      self.fake_cursor = LsnCursor(value)

    def transaction(self):
      return nullcontext()

    def cursor(self):
      return self.fake_cursor

  connection = LsnConnection("0/AB12CD34")

  assert read_flush_lsn(connection) == "0/AB12CD34"
  assert connection.fake_cursor.statements == [
    "SET TRANSACTION READ ONLY",
    "SELECT pg_current_wal_flush_lsn()::text",
  ]

  with pytest.raises(RuntimeError, match="invalid WAL flush LSN"):
    read_flush_lsn(LsnConnection("not-an-lsn"))


def test_app_configuration_check_redacts_secrets_and_matches_roles_and_branch() -> None:
  owner_url = "postgresql://neondb_owner:owner-secret@ep-prod.neon.tech:5432/neondb"
  core_config = json.dumps(
    {
      "DATABASE_URL": "postgresql+psycopg://inkcre_core:core-secret@ep-prod.neon.tech/neondb",
      "JWT_SECRET": "shared-jwt-secret",
      "PEER_ID": str(CORE_PEER_ID),
    }
  )
  postgrest_config = json.dumps(
    {
      "PGRST_DB_URI": "postgresql://authenticator:postgrest-secret@ep-prod.neon.tech/neondb",
      "PGRST_JWT_SECRET": "shared-jwt-secret",
    }
  )

  report = verify_app_configuration(owner_url, core_config, postgrest_config, CORE_APP_NAME)

  assert report == {
    "core_database_matches_neon_branch": True,
    "postgrest_database_matches_neon_branch": True,
    "core_database_role": "inkcre_core",
    "postgrest_database_role": "authenticator",
    "jwt_secrets_match": True,
    "core_peer_id": str(CORE_PEER_ID),
    "expected_core_peer_id": str(CORE_PEER_ID),
  }
  rendered = json.dumps(report)
  assert "owner-secret" not in rendered
  assert "core-secret" not in rendered
  assert "postgrest-secret" not in rendered
  assert "shared-jwt-secret" not in rendered


def test_app_configuration_rejects_wrong_database_branch() -> None:
  owner_url = "postgresql://neondb_owner:owner-secret@ep-prod.neon.tech/neondb"
  core_config = json.dumps(
    {
      "DATABASE_URL": "postgresql://inkcre_core:core-secret@ep-other.neon.tech/neondb",
      "JWT_SECRET": "shared-jwt-secret",
      "PEER_ID": str(CORE_PEER_ID),
    }
  )
  postgrest_config = json.dumps(
    {
      "PGRST_DB_URI": "postgresql://authenticator:postgrest-secret@ep-prod.neon.tech/neondb",
      "PGRST_JWT_SECRET": "shared-jwt-secret",
    }
  )

  with pytest.raises(ValueError, match="selected deployment identity"):
    verify_app_configuration(owner_url, core_config, postgrest_config, CORE_APP_NAME)


def test_app_configuration_rejects_peer_id_outside_canonical_app_identity() -> None:
  owner_url = "postgresql://neondb_owner:owner-secret@ep-prod.neon.tech/neondb"
  core_config = json.dumps(
    {
      "DATABASE_URL": "postgresql://inkcre_core:core-secret@ep-prod.neon.tech/neondb",
      "JWT_SECRET": "shared-jwt-secret",
      "PEER_ID": str(uuid.uuid4()),
    }
  )
  postgrest_config = json.dumps(
    {
      "PGRST_DB_URI": "postgresql://authenticator:postgrest-secret@ep-prod.neon.tech/neondb",
      "PGRST_JWT_SECRET": "shared-jwt-secret",
    }
  )

  with pytest.raises(ValueError, match="selected deployment identity"):
    verify_app_configuration(owner_url, core_config, postgrest_config, CORE_APP_NAME)


def test_checked_in_production_profile_is_reported_as_declared_source_data() -> None:
  profile = checked_in_production_profile(
    Path("deploy/profiles/production.json").read_text(encoding="utf-8")
  )

  assert profile["environment"] == "production"
  assert uuid.UUID(profile["core_peer_id"])
  assert profile["contract_revision"]
  assert profile["migration_head"]
