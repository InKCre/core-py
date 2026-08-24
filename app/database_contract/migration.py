"""Alembic execution behind the database lifecycle interface."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _repository_script() -> ScriptDirectory:
  return ScriptDirectory.from_config(Config(PROJECT_ROOT / "alembic.ini"))


def get_repository_heads() -> tuple[str, ...]:
  """Return the immutable migration heads recorded by this artifact."""
  return tuple(sorted(_repository_script().get_heads()))


def get_repository_revisions() -> frozenset[str]:
  """Return every migration revision that can converge to an artifact head."""
  return frozenset(revision.revision for revision in _repository_script().walk_revisions())


def migrate() -> None:
  """Upgrade the configured database to the artifact's sole head."""
  command.upgrade(Config(PROJECT_ROOT / "alembic.ini"), "head")
