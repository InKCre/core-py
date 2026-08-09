"""Production manifest transitions preserve data while converging catalogs."""

import pytest

from app.database_contract.constants import (
  APPLICATION_TABLES,
  MANIFEST_ADDITIVE_CURRENT_HEAD,
  MANIFEST_ADDITIVE_EMPTY_TABLES,
  MANIFEST_ADDITIVE_PREVIOUS_HEAD,
)
from scripts.database_manifest import validate_manifest_application_tables
from scripts.verify_database_manifest_transition import (
  verify_manifest_transition,
)


def _manifest(
  *,
  schema: str = "inkcre",
  business_rows: int = 10,
  source_types: int = 6,
  registry_tables: bool = True,
  registry_rows: int = 0,
) -> dict[str, object]:
  table_counts = {table: 0 for table in APPLICATION_TABLES}
  table_counts.update(
    {
      "blocks": business_rows,
      "extensions": 6,
      "sources_types": source_types,
      "storage_types": 7,
    }
  )
  if not registry_tables:
    for table in MANIFEST_ADDITIVE_EMPTY_TABLES:
      del table_counts[table]
  else:
    for table in MANIFEST_ADDITIVE_EMPTY_TABLES:
      table_counts[table] = registry_rows

  manifest: dict[str, object] = {
    "alembic_heads": [
      MANIFEST_ADDITIVE_CURRENT_HEAD if registry_tables else MANIFEST_ADDITIVE_PREVIOUS_HEAD
    ],
    "schema": schema,
    "table_counts": table_counts,
  }
  return manifest


def test_allows_only_additive_builtin_catalog_convergence():
  additions = verify_manifest_transition(
    _manifest(registry_tables=False),
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


def test_allows_only_the_two_expected_empty_tables_to_appear():
  assert (
    verify_manifest_transition(
      _manifest(registry_tables=False),
      _manifest(),
    )
    == []
  )


def test_rejects_nonempty_new_registry_tables():
  with pytest.raises(ValueError, match="nonempty_additive_tables"):
    verify_manifest_transition(
      _manifest(registry_tables=False),
      _manifest(registry_rows=1),
    )


def test_rejects_unknown_additive_tables():
  after = _manifest()
  table_counts = after["table_counts"]
  assert isinstance(table_counts, dict)
  table_counts["shadow"] = 0

  with pytest.raises(ValueError, match="unexpected_tables"):
    verify_manifest_transition(
      _manifest(registry_tables=False),
      after,
    )


def test_rejects_unknown_tables_even_when_both_manifests_contain_them():
  before = _manifest()
  after = _manifest()
  for manifest in (before, after):
    table_counts = manifest["table_counts"]
    assert isinstance(table_counts, dict)
    table_counts["shadow"] = 0

  with pytest.raises(ValueError, match="unexpected_tables"):
    verify_manifest_transition(before, after)


def test_allows_an_idempotent_current_head_transition_with_existing_rows():
  assert (
    verify_manifest_transition(
      _manifest(registry_rows=2),
      _manifest(registry_rows=2),
    )
    == []
  )


@pytest.mark.parametrize(
  ("before_head", "after_head"),
  [
    ("unknown", MANIFEST_ADDITIVE_CURRENT_HEAD),
    (MANIFEST_ADDITIVE_PREVIOUS_HEAD, MANIFEST_ADDITIVE_PREVIOUS_HEAD),
  ],
)
def test_rejects_unknown_before_or_stale_after_lineage(before_head, after_head):
  before = _manifest(registry_tables=False)
  after = _manifest()
  before["alembic_heads"] = [before_head]
  after["alembic_heads"] = [after_head]

  with pytest.raises(ValueError, match="alembic_heads"):
    verify_manifest_transition(before, after)


def test_rejects_multi_head_lineage():
  before = _manifest(registry_tables=False)
  before["alembic_heads"] = [MANIFEST_ADDITIVE_PREVIOUS_HEAD, "parallel-head"]

  with pytest.raises(ValueError, match="alembic_heads"):
    verify_manifest_transition(before, _manifest())

  with pytest.raises(ValueError, match="unsupported database manifest lineage"):
    validate_manifest_application_tables(
      set(APPLICATION_TABLES) - MANIFEST_ADDITIVE_EMPTY_TABLES,
      set(APPLICATION_TABLES),
      {MANIFEST_ADDITIVE_PREVIOUS_HEAD, "parallel-head"},
    )


def test_rejects_an_after_manifest_without_the_expected_tables():
  with pytest.raises(ValueError, match="missing_expected_tables"):
    verify_manifest_transition(
      _manifest(registry_tables=False),
      _manifest(registry_tables=False),
    )


def test_database_manifest_accepts_only_complete_old_or_new_table_sets():
  expected = set(APPLICATION_TABLES)
  pre_migration = expected - MANIFEST_ADDITIVE_EMPTY_TABLES

  validate_manifest_application_tables(
    expected,
    expected,
    {MANIFEST_ADDITIVE_CURRENT_HEAD},
  )
  validate_manifest_application_tables(
    pre_migration,
    expected,
    {MANIFEST_ADDITIVE_PREVIOUS_HEAD},
  )

  for actual, head in (
    (expected | {"shadow"}, MANIFEST_ADDITIVE_CURRENT_HEAD),
    (expected - {"blocks"}, MANIFEST_ADDITIVE_CURRENT_HEAD),
    (expected - {"extension_installations"}, MANIFEST_ADDITIVE_CURRENT_HEAD),
    (expected, MANIFEST_ADDITIVE_PREVIOUS_HEAD),
    (pre_migration, MANIFEST_ADDITIVE_CURRENT_HEAD),
    (expected, "unknown"),
  ):
    with pytest.raises(ValueError):
      validate_manifest_application_tables(actual, expected, {head})


def test_rejects_non_protocol_target_schema():
  with pytest.raises(ValueError, match="inkcre schema"):
    verify_manifest_transition(_manifest(), _manifest(schema="public"))


def test_rejects_non_protocol_source_schema():
  with pytest.raises(ValueError, match="source manifest must use the inkcre schema"):
    verify_manifest_transition(_manifest(schema="public"), _manifest())
