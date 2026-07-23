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


def test_production_required_columns_are_not_nullable():
  metadata = get_target_metadata()
  required_columns = {
    ("clients", "config"),
    ("clients", "config_schema"),
    ("logs", "timestamp"),
    ("sources", "config"),
    ("sources", "state"),
    ("sources_collect_jobs", "status"),
    ("sources_types", "config_schema"),
    ("storage_types", "description"),
    ("storage_types", "config_schema"),
    ("storages", "type"),
    ("storages", "config"),
  }

  for table_name, column_name in required_columns:
    assert metadata.tables[table_name].columns[column_name].nullable is False


def test_log_ids_are_bigint():
  metadata = get_target_metadata()

  assert isinstance(metadata.tables["logs"].columns["id"].type, sqlalchemy.BigInteger)


def test_block_storage_foreign_key_preserves_blocks():
  metadata = get_target_metadata()
  storage = metadata.tables["blocks"].columns["storage"]
  foreign_key = next(iter(storage.foreign_keys))

  assert foreign_key.onupdate == "CASCADE"
  assert foreign_key.ondelete == "SET NULL"
