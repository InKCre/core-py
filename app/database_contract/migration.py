"""Alembic execution behind the database lifecycle interface."""

from pathlib import Path

from alembic import command
from alembic.config import Config


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def migrate() -> None:
  """Upgrade the configured database to the artifact's sole head."""
  command.upgrade(Config(PROJECT_ROOT / "alembic.ini"), "head")
