import typing

import pgvector.sqlalchemy
import sqlalchemy

from app.database_contract import PROTOCOL_SCHEMA
from migrations.metadata import get_target_metadata, include_protocol_object


EXPECTED_APPLICATION_TABLES = {
  "agents",
  "ai_dialects",
  "ai_models",
  "ai_providers",
  "block_embeddings",
  "blocks",
  "peers",
  "configs",
  "extensions",
  "embedding_profiles",
  "logs",
  "relation_embeddings",
  "relations",
  "sources",
  "sources_collect_jobs",
  "sources_types",
  "storage_types",
  "storage_blobs",
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
      _table(table_name).columns[column_name].type,
      sqlalchemy.Text,
    )


def test_production_required_columns_are_not_nullable():
  metadata = get_target_metadata()
  required_columns = {
    ("peers", "capabilities"),
    ("peers", "config"),
    ("peers", "config_schema"),
    ("configs", "schema"),
    ("configs", "value"),
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


def test_deployment_configs_are_keyed_json_contract_values():
  table = _table("configs")

  assert set(table.columns.keys()) == {
    "key",
    "schema",
    "value",
    "created_at",
    "updated_at",
  }
  assert isinstance(table.columns["key"].type, sqlalchemy.Text)
  assert isinstance(table.columns["schema"].type, sqlalchemy.Text)
  assert table.primary_key.columns.keys() == ["key"]


def test_ai_registry_and_profile_use_shared_bigint_references():
  dialect = _table("ai_dialects")
  provider = _table("ai_providers")
  model = _table("ai_models")
  profile = _table("embedding_profiles")

  assert dialect.primary_key.columns.keys() == ["id"]
  assert isinstance(provider.columns["id"].type, sqlalchemy.BigInteger)
  assert isinstance(model.columns["id"].type, sqlalchemy.BigInteger)
  assert isinstance(profile.columns["id"].type, sqlalchemy.BigInteger)
  capabilities_type = typing.cast(
    sqlalchemy.TypeDecorator,
    model.columns["capabilities"].type,
  )
  assert isinstance(capabilities_type.impl, sqlalchemy.JSON)
  assert profile.columns["dimensions"].nullable is False


def test_agent_definitions_persist_only_reusable_behavior():
  agent = _table("agents")

  assert set(agent.columns.keys()) == {
    "id",
    "name",
    "system_prompt",
    "tools",
    "tool_choice",
    "model",
    "max_model_calls_per_turn",
    "created_at",
    "updated_at",
  }
  assert isinstance(agent.columns["id"].type, sqlalchemy.BigInteger)
  tools_type = typing.cast(sqlalchemy.TypeDecorator, agent.columns["tools"].type)
  assert isinstance(tools_type.impl, sqlalchemy.ARRAY)
  assert agent.columns["tool_choice"].nullable is True


def test_peers_own_protocol_neutral_identity_snapshot_and_lease():
  peer = _table("peers")

  assert set(peer.columns.keys()) == {
    "id",
    "name",
    "labels",
    "config",
    "config_schema",
    "capabilities",
    "lease_expires_at",
    "created_at",
    "updated_at",
  }
  assert isinstance(peer.columns["id"].type, sqlalchemy.Uuid)
  assert isinstance(peer.columns["capabilities"].type, sqlalchemy.JSON)
  assert peer.columns["lease_expires_at"].nullable is True


def test_embedding_records_are_profile_scoped_variable_vectors():
  block_record = _table("block_embeddings")
  relation_record = _table("relation_embeddings")

  assert block_record.primary_key.columns.keys() == ["profile", "block"]
  assert relation_record.primary_key.columns.keys() == ["profile", "relation"]
  block_vector = typing.cast(
    pgvector.sqlalchemy.VECTOR,
    block_record.columns["embedding"].type,
  )
  relation_vector = typing.cast(
    pgvector.sqlalchemy.VECTOR,
    relation_record.columns["embedding"].type,
  )
  assert block_vector.dim is None
  assert relation_vector.dim is None


def test_storage_blobs_own_only_uuid_pointer_and_binary_bytes():
  table = _table("storage_blobs")

  assert set(table.columns.keys()) == {"id", "data"}
  assert isinstance(table.columns["id"].type, sqlalchemy.Uuid)
  assert isinstance(table.columns["data"].type, sqlalchemy.LargeBinary)
  assert table.columns["data"].nullable is False


def test_block_storage_foreign_key_restricts_catalog_deletion():
  metadata = get_target_metadata()
  storage = _table("blocks").columns["storage"]
  foreign_key = next(iter(storage.foreign_keys))

  assert foreign_key.column.table.schema == PROTOCOL_SCHEMA
  assert foreign_key.onupdate == "CASCADE"
  assert foreign_key.ondelete == "RESTRICT"


def test_autogenerate_ignores_lifecycle_internal_tables():
  protocol_table = sqlalchemy.Table(
    "peers",
    sqlalchemy.MetaData(),
    schema=PROTOCOL_SCHEMA,
  )
  internal_table = sqlalchemy.Table(
    "contract_state",
    sqlalchemy.MetaData(),
    schema="inkcre_internal",
  )

  assert include_protocol_object(protocol_table, "peers", "table", True, None)
  assert not include_protocol_object(
    internal_table,
    "contract_state",
    "table",
    True,
    None,
  )
