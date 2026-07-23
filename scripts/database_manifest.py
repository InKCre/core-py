"""Emit a value-free manifest for database recovery verification."""

import json
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from migrations.metadata import get_target_metadata
from migrations.settings import MigrationSettings
from scripts.sanitize_preview_base import LINEAGE_TABLE, validate_application_tables


def build_database_manifest(database_url: str) -> dict[str, object]:
  """Return migration lineage and row counts without reading row values."""
  normalized_url = MigrationSettings(database_url=database_url).database_url
  expected_tables = set(get_target_metadata().tables)
  engine = create_engine(normalized_url, poolclass=NullPool)

  try:
    with engine.connect() as connection:
      actual_tables = set(
        connection.execute(
          text(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """
          )
        ).scalars()
      )
      validate_application_tables(actual_tables, expected_tables)

      heads = sorted(
        connection.execute(text(f'SELECT version_num FROM "{LINEAGE_TABLE}"')).scalars()
      )
      quote = connection.dialect.identifier_preparer.quote
      counts = {
        table: connection.execute(text(f"SELECT count(*) FROM {quote(table)}")).scalar_one()
        for table in sorted(expected_tables)
      }
      server_version = connection.execute(
        text("SELECT current_setting('server_version_num')")
      ).scalar_one()
  finally:
    engine.dispose()

  return {
    "format": 1,
    "server_version_num": server_version,
    "alembic_heads": heads,
    "table_counts": counts,
  }


def main() -> int:
  database_url = os.getenv("DATABASE_URL")
  if not database_url:
    print("DATABASE_URL is required", file=sys.stderr)
    return 2

  try:
    manifest = build_database_manifest(database_url)
  except (OSError, SQLAlchemyError, ValueError) as error:
    print(f"ERROR: {error}", file=sys.stderr)
    return 1

  print(json.dumps(manifest, indent=2, sort_keys=True))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
