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
