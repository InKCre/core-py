from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_offline_upgrade_requires_only_database_url(
  monkeypatch: pytest.MonkeyPatch,
  tmp_path: Path,
  capsys: pytest.CaptureFixture[str],
):
  monkeypatch.chdir(tmp_path)
  monkeypatch.setenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost/testdb",
  )
  monkeypatch.delenv("JWT_SECRET", raising=False)

  config = Config(PROJECT_ROOT / "alembic.ini")
  config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))

  command.upgrade(config, "head", sql=True)

  offline_sql = capsys.readouterr().out
  assert "CREATE TABLE" in offline_sql
  assert "DROP TABLE inkcre.extension_peer_bindings" in offline_sql
  assert "DROP TABLE inkcre.extension_installations" in offline_sql
  assert "CREATE FUNCTION inkcre.set_extension_peer_enabled" in offline_sql
  assert "REVOKE EXECUTE ON FUNCTION" in offline_sql
  assert "FROM inkcre.clients" in offline_sql
