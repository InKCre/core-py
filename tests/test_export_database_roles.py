"""Password-free role bootstrap artifact."""

import pytest

from scripts.export_database_roles import _attribute_clauses


def test_role_export_maps_portable_attributes_without_passwords():
  assert _attribute_clauses((True, False, False, False, False, False, False)) == (
    "LOGIN",
    "NOINHERIT",
    "NOSUPERUSER",
    "NOCREATEDB",
    "NOCREATEROLE",
    "NOREPLICATION",
    "NOBYPASSRLS",
  )


def test_role_export_rejects_elevated_principals():
  with pytest.raises(ValueError, match="must not have elevated attributes"):
    _attribute_clauses((False, False, True, False, False, False, False))
