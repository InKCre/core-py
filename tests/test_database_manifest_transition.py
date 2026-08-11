"""Hard-cut manifest transition preserves every unrelated relation."""

import pytest

from app.database_contract.constants import (
  APPLICATION_TABLES,
  EXTENSION_CUTOVER_CURRENT_HEAD,
  EXTENSION_CUTOVER_PREVIOUS_HEAD,
  EXTENSION_CUTOVER_RELATIONS,
)
from scripts.database_manifest import validate_manifest_application_tables
from scripts.verify_database_manifest_transition import verify_manifest_transition


def manifest(
  *, previous: bool, business_rows: int = 10, extension_rows: int = 0
) -> dict[str, object]:
  counts = {table: 0 for table in APPLICATION_TABLES}
  counts["blocks"] = business_rows
  counts["sources_types"] = 6
  counts["storage_types"] = 7
  counts["extensions"] = extension_rows
  if previous:
    counts["extension_installations"] = 3
    counts["extension_peer_bindings"] = 4
  return {
    "schema": "inkcre",
    "alembic_heads": [
      EXTENSION_CUTOVER_PREVIOUS_HEAD if previous else EXTENSION_CUTOVER_CURRENT_HEAD
    ],
    "table_counts": counts,
  }


def test_hard_cut_drops_exactly_three_state_relations_and_recreates_empty_canonical():
  assert (
    verify_manifest_transition(
      manifest(previous=True, extension_rows=6),
      manifest(previous=False, extension_rows=0),
    )
    == []
  )


def test_hard_cut_rejects_seeded_canonical_rows_or_unrelated_row_changes():
  with pytest.raises(ValueError, match="extension_reset_invalid"):
    verify_manifest_transition(
      manifest(previous=True), manifest(previous=False, extension_rows=1)
    )
  with pytest.raises(ValueError, match='"table": "blocks"'):
    verify_manifest_transition(
      manifest(previous=True, business_rows=10),
      manifest(previous=False, business_rows=9),
    )


def test_current_head_transition_preserves_extension_rows():
  assert (
    verify_manifest_transition(
      manifest(previous=False, extension_rows=2),
      manifest(previous=False, extension_rows=2),
    )
    == []
  )
  with pytest.raises(ValueError, match='"table": "extensions"'):
    verify_manifest_transition(
      manifest(previous=False, extension_rows=2),
      manifest(previous=False, extension_rows=1),
    )


def test_database_manifest_accepts_only_exact_previous_or_current_shape():
  expected = set(APPLICATION_TABLES)
  previous = expected | (EXTENSION_CUTOVER_RELATIONS - {"extensions"})
  validate_manifest_application_tables(
    previous, expected, {EXTENSION_CUTOVER_PREVIOUS_HEAD}
  )
  validate_manifest_application_tables(expected, expected, {EXTENSION_CUTOVER_CURRENT_HEAD})
  with pytest.raises(ValueError):
    validate_manifest_application_tables(
      previous | {"shadow"}, expected, {EXTENSION_CUTOVER_PREVIOUS_HEAD}
    )


def test_manifest_rejects_non_protocol_schema_and_unknown_lineage():
  before = manifest(previous=True)
  before["schema"] = "public"
  with pytest.raises(ValueError, match="source manifest"):
    verify_manifest_transition(before, manifest(previous=False))
  with pytest.raises(ValueError, match="unsupported database manifest lineage"):
    validate_manifest_application_tables(
      set(APPLICATION_TABLES), set(APPLICATION_TABLES), {"unknown"}
    )
