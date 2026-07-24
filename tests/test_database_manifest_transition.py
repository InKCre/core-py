"""Production manifest transitions preserve data while converging catalogs."""

import pytest

from scripts.verify_database_manifest_transition import (
  verify_manifest_transition,
)


def _manifest(
  *,
  schema: str = "inkcre",
  business_rows: int = 10,
  source_types: int = 6,
) -> dict[str, object]:
  return {
    "schema": schema,
    "table_counts": {
      "blocks": business_rows,
      "extensions": 6,
      "sources_types": source_types,
      "storage_types": 7,
    },
  }


def test_allows_only_additive_builtin_catalog_convergence():
  additions = verify_manifest_transition(
    _manifest(schema="public"),
    _manifest(source_types=7),
  )

  assert additions == [
    {
      "after": 7,
      "before": 6,
      "delta": 1,
      "table": "sources_types",
    }
  ]


@pytest.mark.parametrize(
  ("before", "after"),
  [
    (_manifest(source_types=7), _manifest(source_types=6)),
    (_manifest(business_rows=10), _manifest(business_rows=11)),
    (_manifest(business_rows=10), _manifest(business_rows=9)),
  ],
)
def test_rejects_catalog_loss_or_business_row_count_changes(before, after):
  with pytest.raises(ValueError):
    verify_manifest_transition(before, after)


def test_rejects_table_set_drift():
  after = _manifest()
  table_counts = after["table_counts"]
  assert isinstance(table_counts, dict)
  del table_counts["blocks"]

  with pytest.raises(ValueError, match="missing_tables"):
    verify_manifest_transition(_manifest(), after)


def test_rejects_non_protocol_target_schema():
  with pytest.raises(ValueError, match="inkcre schema"):
    verify_manifest_transition(_manifest(), _manifest(schema="public"))
