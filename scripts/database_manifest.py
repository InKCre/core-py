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
from app.database_contract.constants import (
  EXTENSION_CUTOVER_CURRENT_HEAD,
  EXTENSION_CUTOVER_PREVIOUS_HEAD,
  EXTENSION_CUTOVER_RELATIONS,
  PROTOCOL_SCHEMA,
)
from scripts.sanitize_preview_base import LINEAGE_TABLE


def validate_manifest_application_tables(
  actual_tables: set[str],
  expected_tables: set[str],
  alembic_heads: set[str],
) -> None:
  """Bind the hard-cut predecessor and current table sets to exact lineage."""
  if alembic_heads == {EXTENSION_CUTOVER_PREVIOUS_HEAD}:
    required_tables = expected_tables | (EXTENSION_CUTOVER_RELATIONS - {"extensions"})
  elif alembic_heads == {EXTENSION_CUTOVER_CURRENT_HEAD}:
    required_tables = expected_tables
  else:
    raise ValueError(f"unsupported database manifest lineage: {sorted(alembic_heads)}")

  if actual_tables == required_tables:
    return

  raise ValueError(
    json.dumps(
      {
        "alembic_heads": sorted(alembic_heads),
        "expected_tables": sorted(expected_tables),
        "required_tables": sorted(required_tables),
        "actual_tables": sorted(actual_tables),
      },
      sort_keys=True,
    )
  )


def _resolve_application_schema(
  connection,
  expected_tables: set[str],
  alembic_heads: set[str],
) -> tuple[str, set[str]]:
  candidates: list[tuple[str, set[str]]] = []
  for schema_name in (PROTOCOL_SCHEMA, "public"):
    actual_tables = set(
      connection.execute(
        text(
          """
          SELECT table_name
          FROM information_schema.tables
          WHERE table_schema = :schema
            AND table_type = 'BASE TABLE'
            AND table_name <> :lineage_table
          """
        ),
        {
          "schema": schema_name,
          "lineage_table": LINEAGE_TABLE,
        },
      ).scalars()
    )
    try:
      validate_manifest_application_tables(
        actual_tables,
        expected_tables,
        alembic_heads,
      )
    except ValueError:
      continue
    candidates.append((schema_name, actual_tables))
  if len(candidates) != 1:
    raise ValueError(
      f"expected exactly one complete application schema, found {len(candidates)}"
    )
  return candidates[0]


def build_database_manifest(database_url: str) -> dict[str, object]:
  """Return migration lineage and row counts without reading row values."""
  normalized_url = MigrationSettings(database_url=database_url).database_url
  if normalized_url is None:
    raise ValueError("DATABASE_URL is required")
  expected_tables = {table.name for table in get_target_metadata().tables.values()}
  engine = create_engine(normalized_url, poolclass=NullPool)

  try:
    with engine.connect() as connection:
      heads = sorted(
        connection.execute(
          text(f'SELECT version_num FROM public."{LINEAGE_TABLE}"')
        ).scalars()
      )
      application_schema, actual_tables = _resolve_application_schema(
        connection,
        expected_tables,
        set(heads),
      )
      quote = connection.dialect.identifier_preparer.quote
      counts = {
        table: connection.execute(
          text(f"SELECT count(*) FROM {quote(application_schema)}.{quote(table)}")
        ).scalar_one()
        for table in sorted(actual_tables)
      }
      server_version = connection.execute(
        text("SELECT current_setting('server_version_num')")
      ).scalar_one()
  finally:
    engine.dispose()

  return {
    "format": 2,
    "schema": application_schema,
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
