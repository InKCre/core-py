"""Preview baseline sanitization guard tests."""

import pytest

from scripts.sanitize_preview_base import (
  LINEAGE_TABLE,
  validate_application_tables,
)


APPLICATION_TABLES = {"blocks", "relations"}


def test_table_allowlist_accepts_application_tables_and_lineage():
  validate_application_tables(
    APPLICATION_TABLES | {LINEAGE_TABLE},
    APPLICATION_TABLES,
  )


def test_table_allowlist_rejects_unexpected_table():
  with pytest.raises(ValueError, match="unexpected tables: shadow"):
    validate_application_tables(
      APPLICATION_TABLES | {LINEAGE_TABLE, "shadow"},
      APPLICATION_TABLES,
    )


def test_table_allowlist_rejects_missing_table():
  with pytest.raises(ValueError, match="missing tables: relations"):
    validate_application_tables(
      {"blocks", LINEAGE_TABLE},
      APPLICATION_TABLES,
    )
