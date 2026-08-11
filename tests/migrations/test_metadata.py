import sqlalchemy

from app.database_contract import PROTOCOL_SCHEMA
from migrations.metadata import get_target_metadata, include_protocol_object


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

  assert set(metadata.tables) == {
    f"{PROTOCOL_SCHEMA}.{table_name}" for table_name in EXPECTED_APPLICATION_TABLES
  }
  assert all(table.schema == PROTOCOL_SCHEMA for table in metadata.tables.values())


def _table(table_name: str):
  return get_target_metadata().tables[f"{PROTOCOL_SCHEMA}.{table_name}"]


def test_text_columns_match_the_published_migration_types():
  metadata = get_target_metadata()
  text_columns = {
    ("extensions", "name"),
    ("extensions", "version"),
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
      _table(table_name).columns[column_name].type,
      sqlalchemy.Text,
    )


def test_production_required_columns_are_not_nullable():
  metadata = get_target_metadata()
  required_columns = {
    ("clients", "config"),
    ("clients", "config_schema"),
    ("extensions", "config"),
    ("extensions", "enabled"),
    ("extensions", "name"),
    ("extensions", "version"),
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
    assert _table(table_name).columns[column_name].nullable is False


def test_log_ids_are_bigint():
  metadata = get_target_metadata()

  assert isinstance(_table("logs").columns["id"].type, sqlalchemy.BigInteger)


def test_block_storage_foreign_key_preserves_blocks():
  metadata = get_target_metadata()
  storage = _table("blocks").columns["storage"]
  foreign_key = next(iter(storage.foreign_keys))

  assert foreign_key.column.table.schema == PROTOCOL_SCHEMA
  assert foreign_key.onupdate == "CASCADE"
  assert foreign_key.ondelete == "SET NULL"


def test_autogenerate_ignores_lifecycle_internal_tables():
  protocol_table = sqlalchemy.Table(
    "clients",
    sqlalchemy.MetaData(),
    schema=PROTOCOL_SCHEMA,
  )
  internal_table = sqlalchemy.Table(
    "contract_state",
    sqlalchemy.MetaData(),
    schema="inkcre_internal",
  )

  assert include_protocol_object(protocol_table, "clients", "table", True, None)
  assert not include_protocol_object(
    internal_table,
    "contract_state",
    "table",
    True,
    None,
  )
