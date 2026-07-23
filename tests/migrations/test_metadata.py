import sqlalchemy

from migrations.metadata import get_target_metadata


EXPECTED_APPLICATION_TABLES = {
  "block_embeddings",
  "blocks",
  "clients",
  "extensions",
  "logs",
  "relation_embeddings",
  "relations",
  "sources",
  "sources_collect_jobs",
  "sources_types",
  "storage_types",
  "storages",
}


def test_migration_metadata_registers_every_application_table():
  metadata = get_target_metadata()

  assert set(metadata.tables) == EXPECTED_APPLICATION_TABLES
  assert "logs" in metadata.tables


def test_text_columns_match_the_published_migration_types():
  metadata = get_target_metadata()
  text_columns = {
    ("extensions", "id"),
    ("extensions", "nickname"),
    ("logs", "severity_text"),
    ("logs", "body"),
    ("logs", "trace_id"),
    ("logs", "span_id"),
    ("sources", "nickname"),
    ("storages", "nickname"),
  }

  for table_name, column_name in text_columns:
    assert isinstance(
      metadata.tables[table_name].columns[column_name].type,
      sqlalchemy.Text,
    )
