"""Real PostgreSQL proof for Peer snapshots, database-time lease and discovery."""

import datetime
import os
import uuid

import pytest
import sqlalchemy

from app.business.peer import PeerHTTPInbound, PeerManager
from app.engine import SessionLocal
from app.schemas.peer import PEER_HTTP_PROTOCOL, PeerModel


pytestmark = pytest.mark.skipif(
  not os.getenv("INKCRE_TEST_DATABASE_URL"),
  reason="requires an explicitly selected migrated PostgreSQL runtime",
)

CAPABILITY = "core.peer.integration.v1"


def test_real_snapshot_database_lease_and_candidate_filtering(monkeypatch):
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

    PeerManager.register_self()
    PeerManager.setup_builtin_outbounds()
    PeerManager.register_inbound(PeerHTTPInbound(CAPABILITY, "POST", "/integration-action"))
    with SessionLocal() as db:
      local_row = db.get(PeerModel, local)
      assert local_row is not None
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

    published = PeerManager.publish_self()
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
    expiry = PeerManager.renew_self_lease(45)
    with SessionLocal() as db:
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

    candidates = PeerManager._candidates(CAPABILITY, None)
    assert [candidate.peer.id for candidate in candidates] == [live]
    assert PeerManager._candidates(CAPABILITY, live)[0].peer.id == live
    assert PeerManager._candidates(CAPABILITY, expired) == ()

    PeerManager.clear_self_lease()
    cleared = PeerManager.get(local)
    assert cleared is not None
    assert cleared.lease_expires_at is None
  finally:
    monkeypatch.setattr(PeerManager, "_INBOUNDS", original_inbounds)
    monkeypatch.setattr(PeerManager, "_OUTBOUNDS", original_outbounds)
    monkeypatch.setattr("app.business.peer.main.settings.peer_id", original_peer)
    with SessionLocal() as db:
      db.connection().execute(
        sqlalchemy.text("DELETE FROM inkcre.peers WHERE id = ANY(:ids)"),
        {"ids": list(peer_ids)},
      )
      db.commit()
