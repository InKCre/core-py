"""Exercise only the carrier migration on one fresh task-owned PostgreSQL database."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys

from alembic import command
from alembic.config import Config
import psycopg
from psycopg import sql


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPORT_PATH = HERE / "evidence/migration-roundtrip.json"
DATABASE = "o11y_migration_roundtrip"
BASE_REVISION = "a0465e3b028f"
TARGET_REVISION = "3d9593b0c855"
JOB_TYPE = "o11y-migration-roundtrip"
CARRIER_COLUMNS = ("submission_traceparent", "submission_tracestate")
CARRIER_CONSTRAINTS = {
  "submission_traceparent": "jobs_submission_traceparent_capacity",
  "submission_tracestate": "jobs_submission_tracestate_capacity",
}
LEGACY_LOG_BODY = "o11y-migration-roundtrip-legacy-log"
LEGACY_LOG_TRACE_ID = "legacy.migration.roundtrip"


def _credentials() -> dict[str, str]:
  return json.loads((HERE / "runtime/database-credential.json").read_text())


def _urls(credentials: dict[str, str]) -> tuple[str, str, str]:
  admin_server = f"postgresql://postgres:{credentials['admin']}@127.0.0.1:35432/postgres"
  admin_database = admin_server.rsplit("/", 1)[0] + f"/{DATABASE}"
  core_database = (
    f"postgresql+psycopg://inkcre_core:{credentials['core']}@127.0.0.1:35432/{DATABASE}"
  )
  return admin_server, admin_database, core_database


def _environment(
  credentials: dict[str, str],
  admin_database: str,
  core_database: str,
) -> dict[str, str]:
  return {
    **os.environ,
    "INKCRE_ENV_FILE": "",
    "DATABASE_URL": core_database,
    "MIGRATION_DATABASE_URL": admin_database,
    "JWT_SECRET": credentials["jwt"],
    "CORE_DATABASE_PASSWORD": credentials["core"],
    "POSTGREST_DATABASE_PASSWORD": credentials["rest"],
  }


def _write_report(report: dict[str, object]) -> None:
  REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def _create_fresh_database(admin_server: str) -> None:
  with psycopg.connect(admin_server, autocommit=True) as connection:
    exists = connection.execute(
      "SELECT 1 FROM pg_database WHERE datname = %s", (DATABASE,)
    ).fetchone()
    if exists is not None:
      raise RuntimeError("roundtrip_database_already_exists")
    connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DATABASE)))


def _initialize_runtime_database(environment: dict[str, str]) -> None:
  result = subprocess.run(
    [sys.executable, "scripts/database.py", "init", "--profile", "runtime"],
    cwd=ROOT,
    env=environment,
    capture_output=True,
    check=False,
    text=True,
  )
  if result.returncode != 0:
    raise RuntimeError("runtime_database_initialization_failed")


def _migrate(direction: str, revision: str) -> None:
  config = Config(ROOT / "alembic.ini")
  sink = io.StringIO()
  try:
    with redirect_stdout(sink), redirect_stderr(sink):
      if direction == "upgrade":
        command.upgrade(config, revision)
      else:
        command.downgrade(config, revision)
  except Exception as error:
    raise RuntimeError(f"alembic_{direction}_failed") from error


def _heads(connection: psycopg.Connection) -> tuple[str, ...]:
  return tuple(
    row[0]
    for row in connection.execute(
      "SELECT version_num FROM public.alembic_version ORDER BY version_num"
    ).fetchall()
  )


def _columns(connection: psycopg.Connection) -> set[str]:
  return {
    row[0]
    for row in connection.execute(
      """
      SELECT column_name
      FROM information_schema.columns
      WHERE table_schema = 'inkcre' AND table_name = 'jobs'
      """
    ).fetchall()
  }


def _constraints(connection: psycopg.Connection) -> dict[str, str]:
  names = tuple(CARRIER_CONSTRAINTS.values())
  return dict(
    connection.execute(
      """
      SELECT conname, pg_get_constraintdef(oid)
      FROM pg_constraint
      WHERE conrelid = 'inkcre.jobs'::regclass AND conname = ANY(%s)
      """,
      (list(names),),
    ).fetchall()
  )


def _assert_head(connection: psycopg.Connection, revision: str) -> None:
  if _heads(connection) != (revision,):
    raise AssertionError("unexpected_migration_head")


def _assert_carrier_schema(connection: psycopg.Connection) -> None:
  if not set(CARRIER_COLUMNS) <= _columns(connection):
    raise AssertionError("carrier_columns_missing")
  definitions = _constraints(connection)
  if set(definitions) != set(CARRIER_CONSTRAINTS.values()):
    raise AssertionError("carrier_capacity_constraints_missing")
  if not all("octet_length" in value and "512" in value for value in definitions.values()):
    raise AssertionError("carrier_capacity_constraint_definition_unexpected")


def _insert_legacy_rows(connection: psycopg.Connection) -> tuple[int, int]:
  connection.execute(
    """
    INSERT INTO inkcre.job_types
      (id, description, parameters_schema, default_timeout_seconds)
    VALUES (%s, 'Synthetic legacy migration Job', '{}'::jsonb, 60)
    """,
    (JOB_TYPE,),
  )
  job_id = connection.execute(
    """
    INSERT INTO inkcre.jobs (type, parameters, state, timeout_seconds)
    VALUES (%s, '{}'::jsonb, '{}'::jsonb, 60)
    RETURNING id
    """,
    (JOB_TYPE,),
  ).fetchone()[0]
  log_id = connection.execute(
    """
    INSERT INTO inkcre.logs (severity_number, severity_text, body, trace_id, attributes)
    VALUES (9, 'INFO', %s, %s, '{"probe":"migration-roundtrip"}'::jsonb)
    RETURNING id
    """,
    (LEGACY_LOG_BODY, LEGACY_LOG_TRACE_ID),
  ).fetchone()[0]
  return job_id, log_id


def _legacy_rows_preserved(
  connection: psycopg.Connection, job_id: int, log_id: int
) -> bool:
  job = connection.execute(
    """
    SELECT id, type, parameters, state, timeout_seconds, status
    FROM inkcre.jobs
    WHERE id = %s
    """,
    (job_id,),
  ).fetchone()
  log = connection.execute(
    "SELECT id, body, trace_id, attributes FROM inkcre.logs WHERE id = %s", (log_id,)
  ).fetchone()
  return job == (job_id, JOB_TYPE, {}, {}, 60, "pending") and log == (
    log_id,
    LEGACY_LOG_BODY,
    LEGACY_LOG_TRACE_ID,
    {"probe": "migration-roundtrip"},
  )


def _insert_maximum_carrier(connection: psycopg.Connection) -> int:
  value = "x" * 512
  row = connection.execute(
    """
    INSERT INTO inkcre.jobs
      (
        type,
        parameters,
        state,
        timeout_seconds,
        submission_traceparent,
        submission_tracestate
      )
    VALUES (%s, '{}'::jsonb, '{}'::jsonb, 60, %s, %s)
    RETURNING id
    """,
    (JOB_TYPE, value, value),
  ).fetchone()
  lengths = connection.execute(
    """
    SELECT octet_length(submission_traceparent), octet_length(submission_tracestate)
    FROM inkcre.jobs
    WHERE id = %s
    """,
    (row[0],),
  ).fetchone()
  if lengths != (512, 512):
    raise AssertionError("maximum_carrier_not_preserved")
  return row[0]


def _oversized_carriers_rejected(connection: psycopg.Connection) -> list[str]:
  rejected = []
  for column in CARRIER_COLUMNS:
    statement = sql.SQL(
      """
      INSERT INTO inkcre.jobs (type, parameters, state, timeout_seconds, {})
      VALUES (%s, '{{}}'::jsonb, '{{}}'::jsonb, 60, %s)
      """
    ).format(sql.Identifier(column))
    try:
      connection.execute(statement, (JOB_TYPE, "x" * 513))
    except psycopg.errors.CheckViolation:
      rejected.append(column)
    else:
      raise AssertionError("oversized_carrier_accepted")
  return rejected


def _carrier_values(
  connection: psycopg.Connection, job_id: int
) -> tuple[str | None, str | None]:
  return connection.execute(
    """
    SELECT submission_traceparent, submission_tracestate
    FROM inkcre.jobs
    WHERE id = %s
    """,
    (job_id,),
  ).fetchone()


def main() -> int:
  stage = "load_credentials"
  report: dict[str, object] = {"database": DATABASE, "status": "failed"}
  try:
    credentials = _credentials()
    admin_server, admin_database, core_database = _urls(credentials)
    environment = _environment(credentials, admin_database, core_database)
    os.environ.update(environment)

    stage = "create_fresh_database"
    _create_fresh_database(admin_server)

    stage = "initialize_runtime_database"
    _initialize_runtime_database(environment)
    with psycopg.connect(admin_database, autocommit=True) as connection:
      _assert_head(connection, TARGET_REVISION)

    stage = "downgrade_to_base"
    _migrate("downgrade", BASE_REVISION)
    with psycopg.connect(admin_database, autocommit=True) as connection:
      _assert_head(connection, BASE_REVISION)
      if set(CARRIER_COLUMNS) & _columns(connection):
        raise AssertionError("carrier_columns_present_after_downgrade")
      if _constraints(connection):
        raise AssertionError("carrier_constraints_present_after_downgrade")
      legacy_job_id, legacy_log_id = _insert_legacy_rows(connection)
      if not _legacy_rows_preserved(connection, legacy_job_id, legacy_log_id):
        raise AssertionError("legacy_rows_not_written")

    stage = "upgrade_to_target"
    _migrate("upgrade", TARGET_REVISION)
    with psycopg.connect(admin_database, autocommit=True) as connection:
      _assert_head(connection, TARGET_REVISION)
      _assert_carrier_schema(connection)
      if _carrier_values(connection, legacy_job_id) != (None, None):
        raise AssertionError("legacy_carrier_defaults_not_null")
      legacy_after_first_upgrade = _legacy_rows_preserved(
        connection, legacy_job_id, legacy_log_id
      )
      maximum_carrier_job_id = _insert_maximum_carrier(connection)
      first_capacity_rejections = _oversized_carriers_rejected(connection)

    stage = "downgrade_roundtrip"
    _migrate("downgrade", BASE_REVISION)
    with psycopg.connect(admin_database, autocommit=True) as connection:
      _assert_head(connection, BASE_REVISION)
      if set(CARRIER_COLUMNS) & _columns(connection):
        raise AssertionError("carrier_columns_survived_downgrade")
      legacy_after_downgrade = _legacy_rows_preserved(
        connection, legacy_job_id, legacy_log_id
      )

    stage = "reupgrade_to_target"
    _migrate("upgrade", TARGET_REVISION)
    with psycopg.connect(admin_database, autocommit=True) as connection:
      _assert_head(connection, TARGET_REVISION)
      _assert_carrier_schema(connection)
      if _carrier_values(connection, maximum_carrier_job_id) != (None, None):
        raise AssertionError("downgrade_did_not_remove_carrier")
      legacy_after_reupgrade = _legacy_rows_preserved(
        connection, legacy_job_id, legacy_log_id
      )
      reupgrade_capacity_rejections = _oversized_carriers_rejected(connection)

    report = {
      "database": DATABASE,
      "status": "passed",
      "initial_head": TARGET_REVISION,
      "downgrade_head": BASE_REVISION,
      "reupgrade_head": TARGET_REVISION,
      "legacy_job_id": legacy_job_id,
      "legacy_pg_log_id": legacy_log_id,
      "legacy_job_and_pg_log_preserved": {
        "after_first_upgrade": legacy_after_first_upgrade,
        "after_downgrade": legacy_after_downgrade,
        "after_reupgrade": legacy_after_reupgrade,
      },
      "carrier_columns_and_capacity_checks_present": True,
      "accepted_512_byte_carriers": True,
      "rejected_513_byte_carriers": {
        "after_first_upgrade": first_capacity_rejections,
        "after_reupgrade": reupgrade_capacity_rejections,
      },
      "downgrade_removes_carriers_as_expected": True,
      "reupgrade_restores_columns_with_null_legacy_values": True,
    }
  except Exception as error:
    report = {
      **report,
      "stage": stage,
      "error_type": type(error).__name__,
    }
  _write_report(report)
  print(json.dumps(report, indent=2, sort_keys=True))
  return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
  raise SystemExit(main())
