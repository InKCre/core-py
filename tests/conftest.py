"""Hermetic process environment for the repository test suite."""

import os


os.environ.update(
  {
    "INKCRE_ENV_FILE": "",
    "DATABASE_URL": "postgresql+psycopg://test:test@127.0.0.1:1/test",
    "JWT_SECRET": "test-only-jwt",
    "LLM_SP_AK": "",
    "LLM_SP_BASE_URL": "",
    "OBSRV__LOGGING_BACKEND": "none",
    "SKIP_EXTENSIONS_SYNC": "1",
  }
)
