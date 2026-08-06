"""Alembic execution behind the database lifecycle interface."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_repository_heads() -> tuple[str, ...]:
  """Return the immutable migration heads recorded by this artifact."""
  config = Config(PROJECT_ROOT / "alembic.ini")
  return tuple(sorted(ScriptDirectory.from_config(config).get_heads()))


def migrate() -> None:
  """Upgrade the configured database to the artifact's sole head."""
  command.upgrade(Config(PROJECT_ROOT / "alembic.ini"), "head")
