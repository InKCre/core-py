"""Hermetic tests for application settings."""

from importlib import reload
import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError


TEST_DATABASE_URL = "postgresql+psycopg://user:password@localhost/testdb"
TEST_JWT_SECRET = "test-only-jwt-secret-at-least-32-bytes"  # noqa: S105
TEST_LOGTAIL_TOKEN = "test-only-logtail-token"  # noqa: S105

# Importing app.settings constructs the process-global settings object. Give that import
# deterministic test-only inputs; individual Settings tests disable dotenv explicitly.
os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)
os.environ.setdefault("JWT_SECRET", TEST_JWT_SECRET)
os.environ.setdefault("OBSRV__LOGGING_BACKEND", "none")

import app.settings as settings_module


def build_settings(environment: dict[str, str]):
  """Build Settings from exactly the supplied environment."""
  with patch.dict(os.environ, environment, clear=True):
    return settings_module.Settings(_env_file=None)


def test_settings_with_all_required_vars():
  settings = build_settings(
    {
      "DATABASE_URL": TEST_DATABASE_URL,
      "JWT_SECRET": TEST_JWT_SECRET,
      "HOST": "127.0.0.1",
      "PORT": "9000",
    }
  )

  assert settings.database_url == TEST_DATABASE_URL
  assert settings.jwt_secret == TEST_JWT_SECRET
  assert settings.host == "127.0.0.1"
  assert settings.port == 9000


def test_settings_missing_required_database_url():
  with patch.dict(os.environ, {"JWT_SECRET": TEST_JWT_SECRET}, clear=True):
    with pytest.raises(ValidationError) as error:
      settings_module.Settings(_env_file=None)

  assert [item["loc"] for item in error.value.errors()] == [("database_url",)]


def test_settings_missing_required_jwt_secret():
  with patch.dict(os.environ, {"DATABASE_URL": TEST_DATABASE_URL}, clear=True):
    with pytest.raises(ValidationError) as error:
      settings_module.Settings(_env_file=None)

  assert [item["loc"] for item in error.value.errors()] == [("jwt_secret",)]


def test_settings_default_values():
  settings = build_settings(
    {
      "DATABASE_URL": TEST_DATABASE_URL,
      "JWT_SECRET": TEST_JWT_SECRET,
    }
  )

  assert settings.host == "0.0.0.0"
  assert settings.port == 8000
  assert settings.database_scale_0 is False
  assert settings.peer_name == "core-py"
  assert settings.peer_lease_ttl_seconds == 90
  assert settings.peer_lease_renew_interval_seconds == 30
  assert settings.peer_http_timeout_seconds == 30
  assert settings.semantic_retrieval_maintenance_interval_seconds == 60
  assert settings.semantic_retrieval_maintenance_max_embeddings == 100
  assert settings.semantic_retrieval_maintenance_batch_size == 20
  assert settings.semantic_retrieval_maintenance_scan_page_size == 100
  assert settings.obsrv.logtail_source_token is None
  assert settings.obsrv.logtail_host is None


@pytest.mark.parametrize(
  ("configured", "expected"),
  [
    (
      "postgres://user:password@localhost/testdb",
      "postgresql+psycopg://user:password@localhost/testdb",
    ),
    (
      "postgresql://user:password@localhost/testdb",
      "postgresql+psycopg://user:password@localhost/testdb",
    ),
    (
      "postgresql+psycopg2://user:password@localhost/testdb",
      "postgresql+psycopg://user:password@localhost/testdb",
    ),
    (
      TEST_DATABASE_URL,
      TEST_DATABASE_URL,
    ),
  ],
)
def test_settings_normalize_postgres_scheme(configured: str, expected: str):
  settings = build_settings(
    {
      "DATABASE_URL": configured,
      "JWT_SECRET": TEST_JWT_SECRET,
    }
  )

  assert settings.database_url == expected


@pytest.mark.parametrize("value", ["true", "True", "TRUE", "1", "yes", "Yes", "YES"])
def test_settings_database_scale_0_truthy_values(value: str):
  settings = build_settings(
    {
      "DATABASE_URL": TEST_DATABASE_URL,
      "JWT_SECRET": TEST_JWT_SECRET,
      "DATABASE_SCALE_0": value,
    }
  )

  assert settings.database_scale_0 is True


def test_settings_port_type_conversion():
  settings = build_settings(
    {
      "DATABASE_URL": TEST_DATABASE_URL,
      "JWT_SECRET": TEST_JWT_SECRET,
      "PORT": "3000",
    }
  )

  assert settings.port == 3000
  assert isinstance(settings.port, int)


def test_settings_port_invalid_value():
  with patch.dict(
    os.environ,
    {
      "DATABASE_URL": TEST_DATABASE_URL,
      "JWT_SECRET": TEST_JWT_SECRET,
      "PORT": "not-a-number",
    },
    clear=True,
  ):
    with pytest.raises(ValidationError) as error:
      settings_module.Settings(_env_file=None)

  assert [item["loc"] for item in error.value.errors()] == [("port",)]


def test_settings_environment_names_are_case_insensitive():
  settings = build_settings(
    {
      "database_url": TEST_DATABASE_URL,
      "jwt_secret": TEST_JWT_SECRET,
      "host": "127.0.0.1",
    }
  )

  assert settings.database_url == TEST_DATABASE_URL
  assert settings.jwt_secret == TEST_JWT_SECRET
  assert settings.host == "127.0.0.1"


def test_settings_nested_observability_fields():
  settings = build_settings(
    {
      "DATABASE_URL": TEST_DATABASE_URL,
      "JWT_SECRET": TEST_JWT_SECRET,
      "OBSRV__LOGTAIL_SOURCE_TOKEN": TEST_LOGTAIL_TOKEN,
      "OBSRV__LOGTAIL_HOST": "https://logs.example.com",
    }
  )

  assert settings.obsrv.logtail_source_token == TEST_LOGTAIL_TOKEN
  assert settings.obsrv.logtail_host == "https://logs.example.com"


def test_process_global_settings_instance():
  environment = {
    "INKCRE_ENV_FILE": "",
    "DATABASE_URL": TEST_DATABASE_URL,
    "JWT_SECRET": TEST_JWT_SECRET,
    "OBSRV__LOGGING_BACKEND": "none",
  }
  with patch.dict(os.environ, environment, clear=True):
    reloaded = reload(settings_module)

  assert reloaded.settings.database_url == TEST_DATABASE_URL
  assert reloaded.settings.jwt_secret == TEST_JWT_SECRET


def test_pytest_disables_dotenv_loading():
  assert settings_module.Settings.model_config["env_file"] is None


def test_engine_uses_process_global_settings():
  environment = {
    "INKCRE_ENV_FILE": "",
    "DATABASE_URL": TEST_DATABASE_URL,
    "JWT_SECRET": TEST_JWT_SECRET,
    "DATABASE_SCALE_0": "true",
    "OBSRV__LOGGING_BACKEND": "none",
  }
  with patch.dict(os.environ, environment, clear=True):
    reload(settings_module)
    import app.engine as engine_module

    reloaded_engine = reload(engine_module)

  assert reloaded_engine.DATABASE_URL == TEST_DATABASE_URL
