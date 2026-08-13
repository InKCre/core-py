"""Preview baseline sanitization guard tests."""

import pytest

from scripts.sanitize_preview_base import (
  validate_application_tables,
  validate_source_environment,
)


APPLICATION_TABLES = {"blocks", "relations"}


def test_table_allowlist_accepts_application_tables_and_lineage():
  validate_application_tables(APPLICATION_TABLES, APPLICATION_TABLES)


def test_table_allowlist_rejects_unexpected_table():
  with pytest.raises(ValueError, match="unexpected tables: shadow"):
    validate_application_tables(
      APPLICATION_TABLES | {"shadow"},
      APPLICATION_TABLES,
    )


def test_table_allowlist_rejects_missing_table():
  with pytest.raises(ValueError, match="missing tables: relations"):
    validate_application_tables(
      {"blocks"},
      APPLICATION_TABLES,
    )


@pytest.mark.parametrize("environment", ["production", "runtime"])
def test_source_environment_accepts_production_clone_and_idempotent_rerun(environment):
  validate_source_environment(environment)


@pytest.mark.parametrize("environment", ["preview", "development", "absent"])
def test_source_environment_rejects_other_identities(environment):
  with pytest.raises(ValueError, match="must inherit production"):
    validate_source_environment(environment)
