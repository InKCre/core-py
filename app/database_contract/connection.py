"""Database connections that do not import application runtime settings."""

from collections.abc import Generator
from contextlib import contextmanager

import psycopg

from migrations.settings import MigrationSettings, get_migration_database_url


def normalized_database_url(database_url: str | None = None) -> str:
  """Return the migration URL using the installed psycopg driver."""
  if database_url is None:
    return get_migration_database_url()
  normalized = MigrationSettings(database_url=database_url).database_url
  if normalized is None:
    raise ValueError("DATABASE_URL is required")
  return normalized


def psycopg_database_url(database_url: str | None = None) -> str:
  """Return a libpq-compatible URL without SQLAlchemy's driver marker."""
  return normalized_database_url(database_url).replace(
    "postgresql+psycopg://",
    "postgresql://",
    1,
  )


@contextmanager
def database_connection(
  database_url: str | None = None,
) -> Generator[psycopg.Connection, None, None]:
  """Open a short-lived transaction-capable psycopg connection."""
  with psycopg.connect(psycopg_database_url(database_url)) as connection:
    yield connection
