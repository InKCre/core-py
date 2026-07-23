"""Preview baseline sanitization guard tests."""

import pytest

from scripts.sanitize_preview_base import LINEAGE_TABLE, _validate_tables


APPLICATION_TABLES = {"blocks", "relations"}


def test_table_allowlist_accepts_application_tables_and_lineage():
  _validate_tables(
    APPLICATION_TABLES | {LINEAGE_TABLE},
    APPLICATION_TABLES,
  )


def test_table_allowlist_rejects_unexpected_table():
  with pytest.raises(ValueError, match="unexpected tables: shadow"):
    _validate_tables(
      APPLICATION_TABLES | {LINEAGE_TABLE, "shadow"},
      APPLICATION_TABLES,
    )


def test_table_allowlist_rejects_missing_table():
  with pytest.raises(ValueError, match="missing tables: relations"):
    _validate_tables(
      {"blocks", LINEAGE_TABLE},
      APPLICATION_TABLES,
    )
