import re

import sqlalchemy
from sqlalchemy.dialects import postgresql

from app.database_contract import PROTOCOL_SCHEMA
from app.schemas.extension.registry import (
  REGISTRY_COORDINATE_SEGMENT_PATTERN,
  REGISTRY_SEMVER_PATTERN,
  REGISTRY_TARGET_DIGEST_PATTERN,
  REGISTRY_TARGET_KEY_PATTERN,
)
from migrations.metadata import get_target_metadata


def _table(name: str) -> sqlalchemy.Table:
  return get_target_metadata().tables[f"{PROTOCOL_SCHEMA}.{name}"]


def test_registry_identity_grammars_match_the_public_contract():
  for value in ("a", "inkcre", "twitter-v2", "a" * 64):
    assert re.fullmatch(REGISTRY_COORDINATE_SEGMENT_PATTERN, value)
  for value in ("", "InkCre", "-inkcre", "inkcre-", "ink_cre", "a" * 65):
    assert not re.fullmatch(REGISTRY_COORDINATE_SEGMENT_PATTERN, value)

  for value in ("0.0.0", "1.2.3", "1.2.3-rc.1", "1.2.3-0", "1.2.3-x-y.z"):
    assert re.fullmatch(REGISTRY_SEMVER_PATTERN, value)
  for value in ("v1.2.3", "1.2", "01.2.3", "1.02.3", "1.2.03", "1.2.3-01", "1.2.3+build"):
    assert not re.fullmatch(REGISTRY_SEMVER_PATTERN, value)

  for value in ("a", "python-core-v1", "python.core_v1", "a" * 128):
    assert re.fullmatch(REGISTRY_TARGET_KEY_PATTERN, value)
  for value in ("", "Python", ".python", "python-", "a" * 129):
    assert not re.fullmatch(REGISTRY_TARGET_KEY_PATTERN, value)

  assert re.fullmatch(REGISTRY_TARGET_DIGEST_PATTERN, f"sha256:{'a' * 64}")
  for value in (f"sha256:{'A' * 64}", f"sha256:{'a' * 63}", "a" * 64):
    assert not re.fullmatch(REGISTRY_TARGET_DIGEST_PATTERN, value)


def test_extension_installation_owns_exact_version_and_configuration():
  table = _table("extension_installations")

  assert [column.name for column in table.primary_key.columns] == ["namespace", "name"]
  assert set(table.columns.keys()) == {
    "namespace",
    "name",
    "version",
    "config",
    "config_schema",
  }
  for column_name in ("namespace", "name", "version"):
    assert isinstance(table.columns[column_name].type, sqlalchemy.Text)
    assert table.columns[column_name].nullable is False
  for column_name in ("config", "config_schema"):
    column = table.columns[column_name]
    assert isinstance(column.type, postgresql.JSONB)
    assert column.nullable is False
    server_default = column.server_default
    assert isinstance(server_default, sqlalchemy.schema.DefaultClause)
    assert str(server_default.arg) == "'{}'::jsonb"

  checks = {
    constraint.name: str(constraint.sqltext)
    for constraint in table.constraints
    if isinstance(constraint, sqlalchemy.CheckConstraint)
  }
  assert checks == {
    "extension_installations_name_canonical": (
      f"name ~ '{REGISTRY_COORDINATE_SEGMENT_PATTERN}'"
    ),
    "extension_installations_namespace_canonical": (
      f"namespace ~ '{REGISTRY_COORDINATE_SEGMENT_PATTERN}'"
    ),
    "extension_installations_version_canonical": (f"version ~ '{REGISTRY_SEMVER_PATTERN}'"),
  }
  unique_constraints = {
    constraint.name: [column.name for column in constraint.columns]
    for constraint in table.constraints
    if isinstance(constraint, sqlalchemy.UniqueConstraint)
  }
  assert unique_constraints == {
    "extension_installations_coordinate_version_key": [
      "namespace",
      "name",
      "version",
    ]
  }


def test_extension_peer_binding_pins_one_target_for_one_existing_peer():
  table = _table("extension_peer_bindings")

  assert [column.name for column in table.primary_key.columns] == [
    "namespace",
    "name",
    "peer_id",
  ]
  assert set(table.columns.keys()) == {
    "namespace",
    "name",
    "version",
    "peer_id",
    "target_key",
    "target_digest",
  }
  assert isinstance(table.columns.peer_id.type, sqlalchemy.Uuid)
  assert all(column.nullable is False for column in table.columns)

  foreign_keys = {
    constraint.name: constraint for constraint in table.foreign_key_constraints
  }
  installation = foreign_keys["extension_peer_bindings_installation_fkey"]
  assert installation.ondelete == "RESTRICT"
  assert installation.deferrable is True
  assert installation.initially == "DEFERRED"
  assert [element.parent.name for element in installation.elements] == [
    "namespace",
    "name",
    "version",
  ]
  assert [element.column.table.name for element in installation.elements] == [
    "extension_installations",
    "extension_installations",
    "extension_installations",
  ]
  assert [element.column.name for element in installation.elements] == [
    "namespace",
    "name",
    "version",
  ]

  peer = foreign_keys["extension_peer_bindings_peer_fkey"]
  assert peer.ondelete == "RESTRICT"
  assert [element.parent.name for element in peer.elements] == ["peer_id"]
  assert [element.column.table.name for element in peer.elements] == ["clients"]
  assert [element.column.name for element in peer.elements] == ["id"]

  checks = {
    constraint.name: str(constraint.sqltext)
    for constraint in table.constraints
    if isinstance(constraint, sqlalchemy.CheckConstraint)
  }
  assert checks == {
    "extension_peer_bindings_name_canonical": (
      f"name ~ '{REGISTRY_COORDINATE_SEGMENT_PATTERN}'"
    ),
    "extension_peer_bindings_namespace_canonical": (
      f"namespace ~ '{REGISTRY_COORDINATE_SEGMENT_PATTERN}'"
    ),
    "extension_peer_bindings_target_digest_canonical": (
      f"target_digest ~ '{REGISTRY_TARGET_DIGEST_PATTERN}'"
    ),
    "extension_peer_bindings_target_key_canonical": (
      f"target_key ~ '{REGISTRY_TARGET_KEY_PATTERN}'"
    ),
    "extension_peer_bindings_version_canonical": (f"version ~ '{REGISTRY_SEMVER_PATTERN}'"),
  }
