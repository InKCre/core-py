import json
from contextlib import nullcontext
from pathlib import Path
import uuid

import pytest

from scripts.automation.production_preflight import (
  checked_in_production_profile,
  collect_database_inventory,
  quiescence_conflicts,
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
