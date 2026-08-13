"""Production convergence preserves the complete current database contract."""

import pytest

from app.database_contract.constants import (
  APPLICATION_TABLES,
)
from app.database_contract.migration import get_repository_heads
from scripts.database_manifest import validate_manifest_application_tables
from scripts.verify_database_manifest_transition import verify_manifest_transition


def manifest(*, business_rows: int = 10, extension_rows: int = 0) -> dict[str, object]:
  counts = {table: 0 for table in APPLICATION_TABLES}
  counts["blocks"] = business_rows
  counts["sources_types"] = 6
  counts["storage_types"] = 7
  counts["extensions"] = extension_rows
  return {
    "schema": "inkcre",
    "alembic_heads": list(get_repository_heads()),
    "table_counts": counts,
  }


def test_current_transition_rejects_unrelated_row_changes():
  with pytest.raises(ValueError, match='"table": "blocks"'):
    verify_manifest_transition(
      manifest(business_rows=10),
      manifest(business_rows=9),
    )


def test_current_head_transition_preserves_extension_rows():
  assert (
    verify_manifest_transition(
      manifest(extension_rows=2),
      manifest(extension_rows=2),
    )
    == []
  )
  with pytest.raises(ValueError, match='"table": "extensions"'):
    verify_manifest_transition(
      manifest(extension_rows=2),
      manifest(extension_rows=1),
    )


def test_database_manifest_accepts_only_exact_current_shape_and_lineage():
  expected = set(APPLICATION_TABLES)
  validate_manifest_application_tables(expected, expected, set(get_repository_heads()))
  with pytest.raises(ValueError):
    validate_manifest_application_tables(
      expected | {"shadow"}, expected, set(get_repository_heads())
    )


def test_manifest_rejects_non_protocol_schema_and_unknown_lineage():
  before = manifest()
  before["schema"] = "public"
  with pytest.raises(ValueError, match="source manifest"):
    verify_manifest_transition(before, manifest())
  with pytest.raises(ValueError, match="unsupported database manifest lineage"):
    validate_manifest_application_tables(
      set(APPLICATION_TABLES), set(APPLICATION_TABLES), {"unknown"}
    )


def test_transition_rejects_a_different_artifact_lineage():
  after = manifest()
  after["alembic_heads"] = ["different"]
  with pytest.raises(ValueError, match="after_alembic_heads"):
    verify_manifest_transition(manifest(), after)
