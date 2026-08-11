"""Disposable PostgreSQL proof for the shared atomic peer-enabled RPC."""

from __future__ import annotations

from collections.abc import Iterator
import importlib
import shutil
import socket
import subprocess
import threading
import typing
import uuid

import psycopg
import pytest
import sqlalchemy
import sqlmodel

from app.business.extension.errors import ExtensionStateConflictError
from app.business.extension.state import SQLExtensionStateStore


@pytest.fixture(scope="module")
def postgres_connection_info(tmp_path_factory) -> Iterator[dict[str, object]]:
  initdb = shutil.which("initdb")
  pg_ctl = shutil.which("pg_ctl")
  if initdb is None or pg_ctl is None:
    pytest.skip("disposable PostgreSQL binaries are unavailable")
  root = tmp_path_factory.mktemp("extension-rpc-postgres")
  data = root / "data"
  with socket.socket() as probe:
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
  initialized = subprocess.run(  # noqa: S603 -- resolved local test binary
    [initdb, "--pgdata", str(data), "--auth=trust", "--no-locale", "--encoding=UTF8"],
    check=False,
    capture_output=True,
    text=True,
  )
  assert initialized.returncode == 0, initialized.stderr
  started = subprocess.run(  # noqa: S603 -- resolved local test binary
    [
      pg_ctl,
      "--pgdata",
      str(data),
      "--options",
      f"-F -h 127.0.0.1 -p {port}",
      "--log",
      str(root / "postgres.log"),
      "--wait",
      "start",
    ],
    check=False,
    capture_output=True,
    text=True,
  )
  assert started.returncode == 0, started.stderr
  info: dict[str, object] = {"host": "127.0.0.1", "port": port, "dbname": "postgres"}
  try:
    yield info
  finally:
    subprocess.run(  # noqa: S603 -- stops only this disposable cluster
      [pg_ctl, "--pgdata", str(data), "--wait", "stop"],
      check=False,
      capture_output=True,
      text=True,
    )


@pytest.fixture(scope="module")
def rpc_database(postgres_connection_info, monkeypatch_module):
  migration = importlib.import_module(
    "migrations.versions.b8c1d2e3f4a5_native_extension_distribution_cutover"
  )
  guard_statements: list[str] = []
  monkeypatch_module.setattr(migration.op, "execute", guard_statements.append)
  migration._create_extension_state_guard()
  assert len(guard_statements) == 2
  statements: list[str] = []
  monkeypatch_module.setattr(migration.op, "execute", statements.append)
  migration._create_peer_enable_rpc()
  assert len(statements) == 2
  with psycopg.connect(**postgres_connection_info, autocommit=True) as connection:
    connection.execute("CREATE SCHEMA inkcre")
    connection.execute("CREATE SCHEMA inkcre_internal")
    connection.execute("CREATE ROLE authenticated NOLOGIN")
    connection.execute("CREATE ROLE anonymous NOLOGIN")
    connection.execute("CREATE TABLE inkcre.clients (id uuid PRIMARY KEY)")
    connection.execute(
      """
      CREATE TABLE inkcre.extensions (
        name text PRIMARY KEY,
        version text NOT NULL,
        enabled uuid[] NOT NULL DEFAULT '{}',
        nickname text,
        config jsonb NOT NULL DEFAULT '{}',
        config_schema jsonb
      )
      """
    )
    for statement in guard_statements:
      connection.execute(typing.cast(typing.LiteralString, statement))
    for statement in statements:
      connection.execute(typing.cast(typing.LiteralString, statement))
    connection.execute("GRANT USAGE ON SCHEMA inkcre TO authenticated")
    connection.execute("GRANT SELECT ON inkcre.clients TO authenticated")
    connection.execute("GRANT SELECT, INSERT, DELETE ON inkcre.extensions TO authenticated")
    connection.execute(
      "GRANT UPDATE (version, nickname, config, config_schema) "
      "ON inkcre.extensions TO authenticated"
    )
    connection.execute(
      "GRANT EXECUTE ON FUNCTION "
      "inkcre.set_extension_peer_enabled(text, uuid, boolean) TO authenticated"
    )
    connection.execute("GRANT USAGE ON SCHEMA inkcre TO anonymous")
  return postgres_connection_info


@pytest.fixture(scope="module")
def monkeypatch_module():
  from _pytest.monkeypatch import MonkeyPatch

  patcher = MonkeyPatch()
  yield patcher
  patcher.undo()


def test_rpc_rejects_unknown_peer_without_mutating_row(rpc_database):
  missing_peer = uuid.uuid4()
  with psycopg.connect(**rpc_database, autocommit=True) as connection:
    connection.execute(
      "INSERT INTO inkcre.extensions (name, version) VALUES ('inkcre/test', '1.0.0')"
    )
    returned = connection.execute(
      "SELECT * FROM inkcre.set_extension_peer_enabled(%s, %s, true)",
      ("inkcre/test", missing_peer),
    ).fetchall()
    enabled_row = connection.execute(
      "SELECT enabled FROM inkcre.extensions WHERE name = 'inkcre/test'"
    ).fetchone()
    assert enabled_row is not None
    enabled = enabled_row[0]

  assert returned == []
  assert enabled == []


def test_rpc_atomically_preserves_concurrent_distinct_peer_additions(rpc_database):
  peers = (uuid.uuid4(), uuid.uuid4())
  with psycopg.connect(**rpc_database, autocommit=True) as connection:
    connection.execute("INSERT INTO inkcre.clients (id) VALUES (%s), (%s)", peers)
  barrier = threading.Barrier(2)
  failures: list[Exception] = []

  def enable(peer_id: uuid.UUID) -> None:
    try:
      with psycopg.connect(**rpc_database) as connection:
        barrier.wait()
        connection.execute(
          "SELECT * FROM inkcre.set_extension_peer_enabled(%s, %s, true)",
          ("inkcre/test", peer_id),
        ).fetchall()
        connection.commit()
    except Exception as error:
      failures.append(error)

  threads = [threading.Thread(target=enable, args=(peer,)) for peer in peers]
  for thread in threads:
    thread.start()
  for thread in threads:
    thread.join(timeout=10)
  assert not failures
  assert all(not thread.is_alive() for thread in threads)
  with psycopg.connect(**rpc_database, autocommit=True) as connection:
    enabled_row = connection.execute(
      "SELECT enabled FROM inkcre.extensions WHERE name = 'inkcre/test'"
    ).fetchone()
    assert enabled_row is not None
    enabled = enabled_row[0]
    connection.execute(
      "SELECT * FROM inkcre.set_extension_peer_enabled(%s, %s, true)",
      ("inkcre/test", peers[0]),
    ).fetchall()
    repeated_row = connection.execute(
      "SELECT enabled FROM inkcre.extensions WHERE name = 'inkcre/test'"
    ).fetchone()
    assert repeated_row is not None
    repeated = repeated_row[0]

  assert set(enabled) == set(peers)
  assert repeated.count(peers[0]) == 1


def test_authenticated_can_execute_but_anonymous_cannot_mutate(rpc_database):
  peer = uuid.uuid4()
  with psycopg.connect(**rpc_database, autocommit=True) as connection:
    connection.execute("INSERT INTO inkcre.clients (id) VALUES (%s)", (peer,))
    connection.execute("SET ROLE authenticated")
    connection.execute(
      "SELECT * FROM inkcre.set_extension_peer_enabled(%s, %s, false)",
      ("inkcre/test", peer),
    ).fetchall()
    connection.execute("RESET ROLE")
    connection.execute("SET ROLE anonymous")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
      connection.execute(
        "SELECT * FROM inkcre.set_extension_peer_enabled(%s, %s, true)",
        ("inkcre/test", peer),
      ).fetchall()
    connection.execute("RESET ROLE")
    enabled_row = connection.execute(
      "SELECT enabled FROM inkcre.extensions WHERE name = 'inkcre/test'"
    ).fetchone()
    assert enabled_row is not None
    enabled = enabled_row[0]

  assert peer not in enabled


def test_authenticated_cannot_bypass_rpc_or_insert_enabled_intent(rpc_database):
  peer = uuid.uuid4()
  with psycopg.connect(**rpc_database, autocommit=True) as connection:
    connection.execute("INSERT INTO inkcre.clients (id) VALUES (%s)", (peer,))
    connection.execute("SET ROLE authenticated")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
      connection.execute(
        "UPDATE inkcre.extensions SET enabled = ARRAY[%s]::uuid[] "
        "WHERE name = 'inkcre/test'",
        (peer,),
      )
    with pytest.raises(psycopg.errors.CheckViolation, match="empty on insert"):
      connection.execute(
        "INSERT INTO inkcre.extensions (name, version, enabled) "
        "VALUES ('inkcre/injected', '1.0.0', ARRAY[%s]::uuid[])",
        (peer,),
      )
    connection.execute(
      "UPDATE inkcre.extensions SET config = '{\"safe\": true}'::jsonb "
      "WHERE name = 'inkcre/test'"
    )
    connection.execute("RESET ROLE")


def test_database_blocks_version_change_and_delete_while_enabled(rpc_database):
  peer = uuid.uuid4()
  with psycopg.connect(**rpc_database, autocommit=True) as connection:
    connection.execute("INSERT INTO inkcre.clients (id) VALUES (%s)", (peer,))
    connection.execute(
      "SELECT * FROM inkcre.set_extension_peer_enabled(%s, %s, true)",
      ("inkcre/test", peer),
    )
    with pytest.raises(psycopg.errors.CheckViolation, match="change extension version"):
      connection.execute(
        "UPDATE inkcre.extensions SET version = '2.0.0' WHERE name = 'inkcre/test'"
      )
    with pytest.raises(psycopg.errors.CheckViolation, match="delete extension"):
      connection.execute("DELETE FROM inkcre.extensions WHERE name = 'inkcre/test'")
    connection.execute(
      "SELECT * FROM inkcre.set_extension_peer_enabled(%s, %s, false)",
      ("inkcre/test", peer),
    )


def test_internal_guard_is_not_in_the_postgrest_protocol_schema(rpc_database):
  with psycopg.connect(**rpc_database, autocommit=True) as connection:
    functions = connection.execute(
      "SELECT n.nspname, p.proname FROM pg_proc p "
      "JOIN pg_namespace n ON n.oid = p.pronamespace "
      "WHERE p.proname IN "
      "('set_extension_peer_enabled', 'enforce_extension_state_authority') "
      "ORDER BY n.nspname"
    ).fetchall()

  assert functions == [
    ("inkcre", "set_extension_peer_enabled"),
    ("inkcre_internal", "enforce_extension_state_authority"),
  ]


def test_concurrent_first_install_returns_semantic_conflict(rpc_database):
  name = "inkcre/concurrent"
  database_url = (
    f"postgresql+psycopg://127.0.0.1:{rpc_database['port']}/{rpc_database['dbname']}"
  )
  engine = sqlalchemy.create_engine(database_url)

  def make_session() -> sqlmodel.Session:
    return sqlmodel.Session(engine)

  store = SQLExtensionStateStore(make_session)
  with psycopg.connect(**rpc_database) as first:
    first.execute(
      "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
      (name,),
    )
    first.execute(
      "INSERT INTO inkcre.extensions (name, version, nickname) "
      "VALUES (%s, '1.0.0', 'First')",
      (name,),
    )
    with pytest.raises(ExtensionStateConflictError, match="already in progress"):
      store.install(name, "2.0.0", "Second")
    first.commit()

  state = store.install(name, "1.0.0", "First")
  assert state.version == "1.0.0"
  engine.dispose()
