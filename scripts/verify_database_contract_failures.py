"""Destructive CI probes for fail-closed database readiness behavior."""

import json
from pathlib import Path
import sys

from psycopg import sql


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.database_contract.catalog import seed_development
from app.database_contract.connection import database_connection
from app.database_contract.constants import (
  ANONYMOUS_ROLE,
  AUTHENTICATED_ROLE,
  DEVELOPMENT_CLIENT_ID,
  INTERNAL_SCHEMA,
  PROTOCOL_SCHEMA,
  RESET_CONFIRMATION,
)
from app.database_contract.lifecycle import reset_development
from app.database_contract.readiness import (
  check_database_contract,
  get_repository_heads,
)
from app.database_contract.roles import RoleSecrets, provision_roles


def _require_failure(component: str) -> None:
  readiness = check_database_contract("development")
  if readiness.ready or readiness.components[component]["status"] != "error":
    raise RuntimeError(f"{component} drift did not fail readiness")


def _require_ready() -> None:
  if not check_database_contract("development").ready:
    raise RuntimeError("database contract did not recover after drift probe")


def _set_environment(environment: str) -> None:
  with database_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute(
        sql.SQL("UPDATE {}.contract_state SET environment = %s WHERE singleton").format(
          sql.Identifier(INTERNAL_SCHEMA)
        ),
        (environment,),
      )


def verify_failure_modes() -> list[str]:
  """Mutate one invariant at a time and restore the development baseline."""
  secrets = RoleSecrets.from_environment()
  (expected_head,) = get_repository_heads()
  checks: list[str] = []

  try:
    with database_connection() as connection:
      with connection.cursor() as cursor:
        cursor.execute(
          "UPDATE alembic_version SET version_num = %s",
          ("c4e8a7b6d5f0",),
        )
    _require_failure("migration")
    checks.append("migration_head")
  finally:
    with database_connection() as connection:
      with connection.cursor() as cursor:
        cursor.execute(
          "UPDATE alembic_version SET version_num = %s",
          (expected_head,),
        )

  try:
    with database_connection() as connection:
      with connection.cursor() as cursor:
        cursor.execute(
          sql.SQL("REVOKE SELECT ON {}.clients FROM {}").format(
            sql.Identifier(PROTOCOL_SCHEMA),
            sql.Identifier(AUTHENTICATED_ROLE),
          )
        )
    _require_failure("privileges")
    checks.append("table_acl")
  finally:
    provision_roles(secrets)

  with database_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute(
        sql.SQL("SELECT owner_role FROM {}.contract_state WHERE singleton").format(
          sql.Identifier(INTERNAL_SCHEMA)
        )
      )
      owner_row = cursor.fetchone()
      if owner_row is None:
        raise RuntimeError("database contract owner is missing")
      (owner_role,) = owner_row
  try:
    with database_connection() as connection:
      with connection.cursor() as cursor:
        cursor.execute(
          sql.SQL(
            "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA {} "
            "REVOKE SELECT ON TABLES FROM {}"
          ).format(
            sql.Identifier(owner_role),
            sql.Identifier(PROTOCOL_SCHEMA),
            sql.Identifier(AUTHENTICATED_ROLE),
          )
        )
    _require_failure("privileges")
    checks.append("default_acl")
  finally:
    provision_roles(secrets)

  try:
    with database_connection() as connection:
      with connection.cursor() as cursor:
        cursor.execute(
          sql.SQL("ALTER ROLE {} LOGIN").format(sql.Identifier(ANONYMOUS_ROLE))
        )
    _require_failure("roles")
    checks.append("role_drift")
  finally:
    provision_roles(secrets)

  try:
    with database_connection() as connection:
      with connection.cursor() as cursor:
        cursor.execute(
          sql.SQL("DELETE FROM {}.clients WHERE id = %s").format(
            sql.Identifier(PROTOCOL_SCHEMA)
          ),
          (DEVELOPMENT_CLIENT_ID,),
        )
    _require_failure("seed")
    checks.append("seed")
  finally:
    seed_development()

  try:
    _set_environment("preview")
    try:
      reset_development(RESET_CONFIRMATION, secrets=secrets)
    except ValueError:
      checks.append("non_development_reset")
    else:
      raise RuntimeError("reset accepted a non-development database")
  finally:
    _set_environment("development")

  _require_ready()
  return checks


def main() -> int:
  try:
    checks = verify_failure_modes()
  except Exception:
    print(
      json.dumps(
        {
          "status": "error",
          "surface": "readiness_negative_cases",
          "reason": "acceptance_failed",
        },
        sort_keys=True,
      )
    )
    return 1
  print(
    json.dumps(
      {
        "status": "ok",
        "surface": "readiness_negative_cases",
        "checks": checks,
      },
      sort_keys=True,
    )
  )
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
