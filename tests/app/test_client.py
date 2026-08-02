"""Client bootstrap contract tests."""

from unittest.mock import MagicMock

import sqlalchemy.dialects.postgresql

import app.business.client.main as client_module


def test_self_registration_supplies_required_config_without_overwriting_it(
  monkeypatch,
):
  session = MagicMock()
  session.__enter__.return_value = session
  registered = MagicMock()
  registered.name = client_module.settings.client_name
  registered.id = client_module.settings.client_id
  session.exec.side_effect = [None, MagicMock(one=MagicMock(return_value=registered))]
  monkeypatch.setattr(client_module, "SessionLocal", MagicMock(return_value=session))

  assert client_module.ClientManager.register_self() is registered

  statement = session.exec.call_args_list[0].args[0]
  compiled = statement.compile(
    dialect=sqlalchemy.dialects.postgresql.dialect(),
  )
  insert_parameters = compiled.params
  update_clause = str(compiled).partition("DO UPDATE SET")[2]

  assert insert_parameters["config"] == {}
  assert insert_parameters["config_schema"] == {}
  assert "config =" not in update_clause
  assert "config_schema =" not in update_clause
