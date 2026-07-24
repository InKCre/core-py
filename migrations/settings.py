"""Migration-only runtime settings."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MigrationSettings(BaseSettings):
  """Configuration required to inspect or apply database migrations."""

  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=False,
    extra="ignore",
  )

  database_url: str | None = None
  migration_database_url: str | None = None

  @field_validator("database_url", "migration_database_url")
  @classmethod
  def use_psycopg_driver(cls, value: str | None) -> str | None:
    """Normalize generic PostgreSQL URLs to the installed psycopg driver."""
    if value is None:
      return None
    if value.startswith("postgres://"):
      return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql+psycopg2://"):
      return value.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
      return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


def get_migration_database_url() -> str:
  """Load the database URL without constructing application settings."""
  settings = MigrationSettings()
  selected = settings.migration_database_url or settings.database_url
  if selected is None:
    raise ValueError("DATABASE_URL or MIGRATION_DATABASE_URL is required")
  return selected
