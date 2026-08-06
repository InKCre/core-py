"""Peer bootstrap contract tests."""

from unittest.mock import MagicMock

import sqlalchemy.dialects.postgresql

import app.business.peer.main as peer_module


def test_self_registration_supplies_defaults_without_overwriting_owner_state(
  monkeypatch,
):
  session = MagicMock()
  session.__enter__.return_value = session
  registered = MagicMock()
  registered.name = peer_module.settings.peer_name
  registered.id = peer_module.settings.peer_id
  session.exec.return_value = None
  session.get.return_value = registered
  monkeypatch.setattr(peer_module, "SessionLocal", MagicMock(return_value=session))

  assert peer_module.PeerManager.register_self() is registered

  statement = session.exec.call_args_list[0].args[0]
  compiled = statement.compile(
    dialect=sqlalchemy.dialects.postgresql.dialect(),
  )
  insert_parameters = compiled.params
  update_clause = str(compiled).partition("DO UPDATE SET")[2]

  assert insert_parameters["config"] == {}
  assert insert_parameters["capabilities"] == []
  assert "config =" not in update_clause
  assert "capabilities =" not in update_clause
  assert "lease_expires_at =" not in update_clause
