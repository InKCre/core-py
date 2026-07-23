"""Create a data-free, lineage-preserving baseline for preview branches."""

import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from migrations.metadata import get_target_metadata
from migrations.settings import MigrationSettings


SANITIZE_GUARD = "ALLOW_PREVIEW_BASE_SANITIZE"
EXPECTED_BRANCH_NAME = "preview-base"
LINEAGE_TABLE = "alembic_version"


def _repository_heads() -> tuple[str, ...]:
  config = Config(PROJECT_ROOT / "alembic.ini")
  return tuple(sorted(ScriptDirectory.from_config(config).get_heads()))


def validate_application_tables(actual: set[str], expected: set[str]) -> None:
  """Require the exact managed application table set and Alembic lineage."""
  if actual != expected | {LINEAGE_TABLE}:
    missing = sorted((expected | {LINEAGE_TABLE}) - actual)
    unexpected = sorted(actual - (expected | {LINEAGE_TABLE}))
    details = []
    if missing:
      details.append(f"missing tables: {', '.join(missing)}")
    if unexpected:
      details.append(f"unexpected tables: {', '.join(unexpected)}")
    raise ValueError("; ".join(details))


def sanitize_preview_base(database_url: str) -> tuple[str, ...]:
  """Truncate known application tables while preserving Alembic lineage."""
  if os.getenv(SANITIZE_GUARD) != "1":
    raise ValueError(f"{SANITIZE_GUARD}=1 is required")
  if os.getenv("PREVIEW_BASE_BRANCH_NAME") != EXPECTED_BRANCH_NAME:
    raise ValueError(f"PREVIEW_BASE_BRANCH_NAME must be {EXPECTED_BRANCH_NAME}")

  normalized_url = MigrationSettings(database_url=database_url).database_url
  expected_tables = set(get_target_metadata().tables)
  expected_heads = _repository_heads()
  engine = create_engine(normalized_url, poolclass=NullPool)

  try:
    with engine.begin() as connection:
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

      current_heads = tuple(
        sorted(
          connection.execute(text("SELECT version_num FROM alembic_version")).scalars()
        )
      )
      if current_heads != expected_heads:
        raise ValueError("preview base is not at the repository Alembic head")

      quoted_tables = ", ".join(f'"{table}"' for table in sorted(expected_tables))
      connection.execute(text(f"TRUNCATE TABLE {quoted_tables} RESTART IDENTITY CASCADE"))

      for table in sorted(expected_tables):
        remaining = connection.execute(text(f'SELECT count(*) FROM "{table}"')).scalar_one()
        if remaining:
          raise RuntimeError(f"table {table} was not sanitized")
  finally:
    engine.dispose()

  return expected_heads


def main() -> int:
  database_url = os.getenv("DATABASE_URL")
  if not database_url:
    print("DATABASE_URL is required", file=sys.stderr)
    return 2

  try:
    heads = sanitize_preview_base(database_url)
  except (OSError, RuntimeError, SQLAlchemyError, ValueError) as error:
    print(f"ERROR: {error}", file=sys.stderr)
    return 1

  print(f"Sanitized preview-base at: {', '.join(heads)}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
