"""Tests for the settings module."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSettings:
    """Test settings configuration management."""

    def test_settings_with_all_required_vars(self):
        """Test that settings can be created with all required environment variables."""
        env_vars = {
            "DATABASE_URL": "postgresql://user:password@localhost:5432/testdb",
            "JWT_SECRET": "test_secret_key_123",
            "HOST": "127.0.0.1",
            "PORT": "9000",
            "LLM_SP_AK": "test_api_key",
            "LLM_SP_BASE_URL": "https://api.test.com",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            # Import fresh settings instance
            from importlib import reload
            import app.settings as settings_module

            reload(settings_module)

            settings = settings_module.Settings()

            assert (
                settings.database_url == "postgresql://user:password@localhost:5432/testdb"
            )
            assert settings.jwt_secret == "test_secret_key_123"
            assert settings.host == "127.0.0.1"
            assert settings.port == 9000
            assert settings.llm_sp_ak == "test_api_key"
            assert settings.llm_sp_base_url == "https://api.test.com"

    def test_settings_missing_required_database_url(self):
        """Test that settings raises error when DATABASE_URL is missing."""
        env_vars = {
            "JWT_SECRET": "test_secret",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from importlib import reload
            import app.settings as settings_module

            reload(settings_module)

            with pytest.raises(ValidationError) as exc_info:
                settings_module.Settings()

            # Check that the error is about DATABASE_URL
            assert "database_url" in str(exc_info.value).lower()

    def test_settings_missing_required_jwt_secret(self):
        """Test that settings raises error when JWT_SECRET is missing."""
        env_vars = {
            "DATABASE_URL": "postgresql://localhost/testdb",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from importlib import reload
            import app.settings as settings_module

            reload(settings_module)

            with pytest.raises(ValidationError) as exc_info:
                settings_module.Settings()

            # Check that the error is about JWT_SECRET
            assert "jwt_secret" in str(exc_info.value).lower()

    def test_settings_default_values(self):
        """Test that settings uses default values for optional fields."""
        env_vars = {
            "DATABASE_URL": "postgresql://localhost/testdb",
            "JWT_SECRET": "test_secret",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from importlib import reload
            import app.settings as settings_module

            reload(settings_module)

            settings = settings_module.Settings()

            # Check defaults
            assert settings.host == "0.0.0.0"
            assert settings.port == 8000
            assert settings.database_scale_0 is False
            assert settings.llm_sp_ak == ""
            assert settings.llm_sp_base_url == ""
            assert settings.obsrv.logtail_source_token is None
            assert settings.obsrv.logtail_host is None

    def test_settings_postgres_to_postgresql_conversion(self):
        """Test that postgres:// scheme is converted to postgresql://."""
        env_vars = {
            "DATABASE_URL": "postgres://user:password@localhost:5432/testdb",
            "JWT_SECRET": "test_secret",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from importlib import reload
            import app.settings as settings_module

            reload(settings_module)

            settings = settings_module.Settings()

            # Should be converted to postgresql://
            assert (
                settings.database_url == "postgresql://user:password@localhost:5432/testdb"
            )
            assert settings.database_url.startswith("postgresql://")

    def test_settings_postgresql_scheme_unchanged(self):
        """Test that postgresql:// scheme is not modified."""
        env_vars = {
            "DATABASE_URL": "postgresql://user:password@localhost:5432/testdb",
            "JWT_SECRET": "test_secret",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from importlib import reload
            import app.settings as settings_module

            reload(settings_module)

            settings = settings_module.Settings()

            # Should remain as postgresql://
            assert (
                settings.database_url == "postgresql://user:password@localhost:5432/testdb"
            )

    def test_settings_database_scale_0_true(self):
        """Test that DATABASE_SCALE_0 can be set to true."""
        env_vars = {
            "DATABASE_URL": "postgresql://localhost/testdb",
            "JWT_SECRET": "test_secret",
            "DATABASE_SCALE_0": "true",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from importlib import reload
            import app.settings as settings_module

            reload(settings_module)

            settings = settings_module.Settings()

            assert settings.database_scale_0 is True

    def test_settings_database_scale_0_various_truthy_values(self):
        """Test that DATABASE_SCALE_0 accepts various truthy values."""
        for value in ["true", "True", "TRUE", "1", "yes", "Yes", "YES"]:
            env_vars = {
                "DATABASE_URL": "postgresql://localhost/testdb",
                "JWT_SECRET": "test_secret",
                "DATABASE_SCALE_0": value,
            }

            with patch.dict(os.environ, env_vars, clear=True):
                from importlib import reload
                import app.settings as settings_module

                reload(settings_module)

                settings = settings_module.Settings()

                assert settings.database_scale_0 is True, f"Failed for value: {value}"

    def test_settings_port_type_conversion(self):
        """Test that PORT is correctly converted to integer."""
        env_vars = {
            "DATABASE_URL": "postgresql://localhost/testdb",
            "JWT_SECRET": "test_secret",
            "PORT": "3000",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from importlib import reload
            import app.settings as settings_module

            reload(settings_module)

            settings = settings_module.Settings()

            assert settings.port == 3000
            assert isinstance(settings.port, int)

    def test_settings_port_invalid_value(self):
        """Test that invalid PORT value raises error."""
        env_vars = {
            "DATABASE_URL": "postgresql://localhost/testdb",
            "JWT_SECRET": "test_secret",
            "PORT": "not_a_number",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from importlib import reload
            import app.settings as settings_module

            reload(settings_module)

            with pytest.raises(ValidationError) as exc_info:
                settings_module.Settings()

            assert "port" in str(exc_info.value).lower()

    def test_settings_case_insensitive(self):
        """Test that environment variable names are case insensitive."""
        env_vars = {
            "database_url": "postgresql://localhost/testdb",  # lowercase
            "jwt_secret": "test_secret",  # lowercase
            "host": "127.0.0.1",  # lowercase
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from importlib import reload
            import app.settings as settings_module

            reload(settings_module)

            settings = settings_module.Settings()

            assert settings.database_url == "postgresql://localhost/testdb"
            assert settings.jwt_secret == "test_secret"
            assert settings.host == "127.0.0.1"

    def test_settings_optional_logtail_fields(self):
        """Test that optional logtail fields can be set."""
        env_vars = {
            "DATABASE_URL": "postgresql://localhost/testdb",
            "JWT_SECRET": "test_secret",
            "LOGTAIL_SOURCE_TOKEN": "test_token_123",
            "LOGTAIL_HOST": "https://logs.example.com",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from importlib import reload
            import app.settings as settings_module

            reload(settings_module)

            settings = settings_module.Settings()

            assert settings.obsrv.logtail_source_token == "test_token_123"
            assert settings.obsrv.logtail_host == "https://logs.example.com"

    def test_settings_global_instance(self):
        """Test that the global settings instance is accessible."""
        env_vars = {
            "DATABASE_URL": "postgresql://localhost/testdb",
            "JWT_SECRET": "test_secret",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from importlib import reload
            import app.settings as settings_module

            reload(settings_module)

            # Should be able to import settings directly
            from app.settings import settings

            assert settings.database_url == "postgresql://localhost/testdb"
            assert settings.jwt_secret == "test_secret"


class TestSettingsIntegration:
    """Test settings integration with other modules."""

    def test_settings_used_in_engine(self):
        """Test that engine module uses settings correctly."""
        env_vars = {
            "DATABASE_URL": "postgresql://localhost/testdb",
            "JWT_SECRET": "test_secret",
            "DATABASE_SCALE_0": "true",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from importlib import reload
            import app.settings as settings_module
            import app.engine as engine_module

            reload(settings_module)
            reload(engine_module)

            # engine should use settings directly
            assert engine_module.DATABASE_URL == "postgresql://localhost/testdb"

    def test_settings_used_in_logging_config(self):
        """Test that logging config uses settings correctly."""
        env_vars = {
            "DATABASE_URL": "postgresql://localhost/testdb",
            "JWT_SECRET": "test_secret",
            "LOGTAIL_SOURCE_TOKEN": "test_token",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            from importlib import reload
            import app.settings as settings_module

            reload(settings_module)

            from app.settings import settings

            # Settings should have logtail token
            assert settings.obsrv.logtail_source_token == "test_token"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
