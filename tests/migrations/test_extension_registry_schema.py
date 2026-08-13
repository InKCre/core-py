"""Canonical Extension state schema tests."""

import sqlalchemy

from app.database_contract import PROTOCOL_SCHEMA
from app.schemas.extension import (
  EXTENSION_NAME_PATTERN,
  EXTENSION_SEMVER_PATTERN,
)
from migrations.metadata import get_target_metadata


def test_canonical_extensions_relation_is_the_only_extension_state_model():
  table = get_target_metadata().tables[f"{PROTOCOL_SCHEMA}.extensions"]

  assert list(table.columns) == [
    table.c.name,
    table.c.version,
    table.c.enabled,
    table.c.nickname,
    table.c.config,
    table.c.config_schema,
  ]
  assert list(table.primary_key.columns) == [table.c.name]
  assert table.c.nickname.nullable
  assert table.c.config_schema.nullable
  assert not table.c.version.nullable
  assert not table.c.enabled.nullable
  assert not table.c.config.nullable
  assert "extension_installations" not in {
    candidate.name for candidate in get_target_metadata().tables.values()
  }
  assert "extension_peer_bindings" not in {
    candidate.name for candidate in get_target_metadata().tables.values()
  }


def test_canonical_extensions_constraints_match_public_validators():
  table = get_target_metadata().tables[f"{PROTOCOL_SCHEMA}.extensions"]
  constraints = {
    item.name: str(item.sqltext)
    for item in table.constraints
    if isinstance(item, sqlalchemy.CheckConstraint)
  }

  assert constraints == {
    "extensions_name_canonical": f"name ~ '{EXTENSION_NAME_PATTERN}'",
    "extensions_version_canonical": f"version ~ '{EXTENSION_SEMVER_PATTERN}'",
  }
