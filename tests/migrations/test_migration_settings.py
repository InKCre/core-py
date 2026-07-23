import ast
from pathlib import Path

import pytest
from pydantic import ValidationError

from migrations.settings import MigrationSettings


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
  ("configured", "expected"),
  [
    (
      "postgres://user:password@localhost/database",
      "postgresql+psycopg://user:password@localhost/database",
    ),
    (
      "postgresql://user:password@localhost/database",
      "postgresql+psycopg://user:password@localhost/database",
    ),
    (
      "postgresql+psycopg://user:password@localhost/database",
      "postgresql+psycopg://user:password@localhost/database",
    ),
    (
      "postgresql+psycopg2://user:password@localhost/database",
      "postgresql+psycopg://user:password@localhost/database",
    ),
  ],
)
def test_migration_settings_normalize_to_psycopg(
  monkeypatch: pytest.MonkeyPatch,
  configured: str,
  expected: str,
):
  monkeypatch.setenv("DATABASE_URL", configured)
  monkeypatch.delenv("JWT_SECRET", raising=False)

  settings = MigrationSettings(_env_file=None)

  assert settings.database_url == expected


def test_migration_settings_require_only_database_url(monkeypatch: pytest.MonkeyPatch):
  monkeypatch.delenv("DATABASE_URL", raising=False)
  monkeypatch.delenv("JWT_SECRET", raising=False)

  with pytest.raises(ValidationError) as error:
    MigrationSettings(_env_file=None)

  assert [item["loc"] for item in error.value.errors()] == [("database_url",)]


def test_alembic_environment_does_not_import_application_settings():
  source = (PROJECT_ROOT / "migrations" / "env.py").read_text()
  imported_modules = {
    node.module
    for node in ast.walk(ast.parse(source))
    if isinstance(node, ast.ImportFrom)
  }

  assert "app.settings" not in imported_modules
