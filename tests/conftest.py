"""Hermetic process environment for the repository test suite."""

import os
from pathlib import Path
import runpy

import pytest


database_url = os.environ.get(
  "INKCRE_TEST_DATABASE_URL",
  "postgresql+psycopg://test:test@127.0.0.1:1/test",
)

os.environ.update(
  {
    "INKCRE_ENV_FILE": "",
    "DATABASE_URL": database_url,
    "JWT_SECRET": "test-only-jwt-secret-at-least-32-bytes",
    "LLM_SP_AK": "",
    "LLM_SP_BASE_URL": "",
    "OBSRV__LOGGING_BACKEND": "none",
    "SKIP_EXTENSIONS_SYNC": "1",
  }
)


@pytest.fixture(scope="session")
def semantic_content_assets() -> Path:
  """Generate ignored real-format samples only when a test module needs them."""
  asset_directory = Path(__file__).parent / "assets" / "semantic-content"
  namespace = runpy.run_path(
    str(asset_directory / "generate_assets.py"),
    run_name="semantic_content_asset_generator",
  )
  generate = namespace["main"]
  if not callable(generate):
    raise RuntimeError("semantic-content asset generator has no callable main")
  generate()
  return asset_directory
