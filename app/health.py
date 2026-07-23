"""Provider-neutral database readiness checks."""

from dataclasses import asdict, dataclass
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from migrations.settings import get_migration_database_url


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DatabaseReadiness:
  """Sanitized result of a read-only database readiness check."""

  ready: bool
  reason: str
  expected_heads: tuple[str, ...]
  current_heads: tuple[str, ...] = ()

  def as_dict(self) -> dict[str, object]:
    """Return JSON-safe probe output."""
    return asdict(self)


def get_repository_heads() -> tuple[str, ...]:
  """Return the immutable migration heads recorded by this artifact."""
  config = Config(PROJECT_ROOT / "alembic.ini")
  script = ScriptDirectory.from_config(config)
  return tuple(sorted(script.get_heads()))


def check_database_readiness(database_url: str | None = None) -> DatabaseReadiness:
  """Check connectivity and migration compatibility without changing the database."""
  expected_heads = get_repository_heads()
  engine = None

  try:
    engine = create_engine(
      database_url or get_migration_database_url(),
      poolclass=NullPool,
    )
    with engine.connect() as connection:
      connection.execute(text("SELECT 1"))
      current_heads = tuple(
        sorted(
          connection.execute(text("SELECT version_num FROM alembic_version")).scalars()
        )
      )
  except Exception:
    return DatabaseReadiness(
      ready=False,
      reason="database_unreachable_or_migration_state_unavailable",
      expected_heads=expected_heads,
    )
  finally:
    if engine is not None:
      engine.dispose()

  if current_heads != expected_heads:
    return DatabaseReadiness(
      ready=False,
      reason="migration_head_mismatch",
      expected_heads=expected_heads,
      current_heads=current_heads,
    )

  return DatabaseReadiness(
    ready=True,
    reason="ready",
    expected_heads=expected_heads,
    current_heads=current_heads,
  )
