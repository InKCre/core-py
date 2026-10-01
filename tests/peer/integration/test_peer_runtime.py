"""Real PostgreSQL proof for Peer snapshots, database-time lease and discovery."""

import datetime
import os
import time
import uuid

import pytest
import sqlalchemy

from app.business.peer import PeerHTTPInbound, PeerManager
from tests.database import TestSession
from app.schemas.peer import PEER_HTTP_PROTOCOL, PeerModel
from app.version import APPLICATION_VERSION


pytestmark = pytest.mark.skipif(
  not os.getenv("INKCRE_TEST_DATABASE_URL"),
  reason="requires an explicitly selected migrated PostgreSQL runtime",
)

CAPABILITY = "core.peer.integration.v1"


def test_real_snapshot_database_lease_and_candidate_filtering(monkeypatch, async_runner):
  original_peer = PeerManager.get_current_peer_ref()
  original_inbounds = PeerManager._INBOUNDS
  original_outbounds = PeerManager._OUTBOUNDS
  local = uuid.uuid4()
  live = uuid.uuid4()
  expired = uuid.uuid4()
  malformed = uuid.uuid4()
  peer_ids = (local, live, expired, malformed)
  try:
    monkeypatch.setattr(PeerManager, "_INBOUNDS", {})
    monkeypatch.setattr(PeerManager, "_OUTBOUNDS", {})
    monkeypatch.setattr("app.business.peer.main.settings.peer_id", local)
    monkeypatch.setattr("app.business.peer.main.settings.peer_name", "integration-local")

    async_runner.run(PeerManager.register_self())
    PeerManager.setup_builtin_outbounds()
    PeerManager.register_inbound(PeerHTTPInbound(CAPABILITY, "POST", "/integration-action"))
    with TestSession() as db:
      local_row = db.get(PeerModel, local)
      assert local_row is not None
      assert local_row.application_version == APPLICATION_VERSION
      local_row.name = "Human name"
      local_row.application_version = "0.0.0"
      local_row.config = {"http_public_base_url": "https://local.example/root/"}
      db.add(local_row)
      now = (
        db.connection()
        .execute(sqlalchemy.select(sqlalchemy.func.statement_timestamp()))
        .scalar_one()
      )
      advertisement = {
        "id": CAPABILITY,
        "inbound": {
          "protocol": PEER_HTTP_PROTOCOL,
          "parameters": {
            "method": "POST",
            "url": "https://remote.example/integration-action",
          },
        },
      }
      db.add(
        PeerModel(
          id=live,
          name="live",
          capabilities=[advertisement],
          lease_expires_at=now + datetime.timedelta(minutes=1),
        )
      )
      db.add(
        PeerModel(
          id=expired,
          name="expired",
          capabilities=[advertisement],
          lease_expires_at=now - datetime.timedelta(seconds=1),
        )
      )
      db.add(
        PeerModel(
          id=malformed,
          name="malformed",
          capabilities=[{"id": CAPABILITY}],
          lease_expires_at=now + datetime.timedelta(minutes=1),
        )
      )
      db.commit()

    registered_again = async_runner.run(PeerManager.register_self())
    assert registered_again.name == "Human name"
    assert registered_again.application_version == APPLICATION_VERSION

    published = async_runner.run(PeerManager.publish_self())
    assert published.capabilities == [
      {
        "id": CAPABILITY,
        "inbound": {
          "protocol": PEER_HTTP_PROTOCOL,
          "parameters": {
            "method": "POST",
            "url": "https://local.example/root/integration-action",
          },
        },
      }
    ]
    expiry = async_runner.run(PeerManager.renew_self_lease(45))
    with TestSession() as db:
      remaining = (
        db.connection()
        .execute(
          sqlalchemy.select(
            sqlalchemy.func.extract(
              "epoch",
              expiry - sqlalchemy.func.statement_timestamp(),
            )
          )
        )
        .scalar_one()
      )
    assert 40 < float(remaining) <= 45

    candidates = async_runner.run(PeerManager._candidates(CAPABILITY, None))
    assert [candidate.peer.id for candidate in candidates] == [live]
    assert async_runner.run(PeerManager._candidates(CAPABILITY, live))[0].peer.id == live
    assert async_runner.run(PeerManager._candidates(CAPABILITY, expired)) == ()

    async_runner.run(PeerManager.clear_self_lease())
    cleared = async_runner.run(PeerManager.get_async(local))
    assert cleared is not None
    assert cleared.lease_expires_at is None
  finally:
    monkeypatch.setattr(PeerManager, "_INBOUNDS", original_inbounds)
    monkeypatch.setattr(PeerManager, "_OUTBOUNDS", original_outbounds)
    monkeypatch.setattr("app.business.peer.main.settings.peer_id", original_peer)
    with TestSession() as db:
      db.connection().execute(
        sqlalchemy.text("DELETE FROM inkcre.peers WHERE id = ANY(:ids)"),
        {"ids": list(peer_ids)},
      )
      db.commit()


def test_failed_cold_restore_preserves_intent_and_reports_not_ready(monkeypatch):
  """A real Registry failure must not publish an executable Peer lease."""
  from fastapi.testclient import TestClient

  import run
  from app.schemas.extension import ExtensionModel

  peer = uuid.uuid4()
  name = f"issue121/missing-{peer.hex}"
  monkeypatch.setattr("app.settings.settings.peer_id", peer)
  monkeypatch.setattr(run, "SKIP_EXTENSION_START", False)
  with TestSession() as db:
    db.add(
      PeerModel(
        id=peer,
        name="failed-restore-test",
        config={"extension_registry_url": "http://127.0.0.1:1"},
      )
    )
    db.add(ExtensionModel(name=name, version="0.0.0"))
    db.flush()
    db.connection().execute(
      sqlalchemy.text("SELECT inkcre.set_extension_peer_enabled(:name, :peer, true)"),
      {"name": name, "peer": peer},
    )
    db.commit()
  try:
    with TestClient(run.api_app) as client:
      deadline = time.monotonic() + 10
      while True:
        response = client.get("/readyz")
        runtime = response.json()["runtime"]
        if runtime["phase"] == "failed":
          break
        assert time.monotonic() < deadline, runtime
        time.sleep(0.02)
      assert response.status_code == 503
      assert runtime == {
        "phase": "failed",
        "reason": "runtime_bootstrap_failed",
        "step": "extensions",
      }
      assert client.get("/livez").status_code == 200
      with TestSession() as db:
        installed = db.get(ExtensionModel, name)
        assert installed is not None and peer in installed.enabled
        registered = db.get(PeerModel, peer)
        assert registered is not None and registered.lease_expires_at is None
  finally:
    with TestSession() as db:
      db.connection().execute(
        sqlalchemy.text("SELECT inkcre.set_extension_peer_enabled(:name, :peer, false)"),
        {"name": name, "peer": peer},
      )
      db.connection().execute(
        sqlalchemy.text("DELETE FROM inkcre.extensions WHERE name = :name"),
        {"name": name},
      )
      db.connection().execute(
        sqlalchemy.text("DELETE FROM inkcre.peers WHERE id = :peer"), {"peer": peer}
      )
      db.commit()
