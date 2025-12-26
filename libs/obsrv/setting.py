"""Observability settings."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class ObsrvSetting(BaseSettings):
  """Observability settings."""

  logging_backend: Optional[str] = Field(
    default="postgresql",
    description="Logging backend to use (e.g., 'logtail', 'postgresql')",
  )
  logging_backend_level: int = Field(
    default=20,
    description="Minimum log level for sending logs to the backend",
  )
  logtail_source_token: Optional[str] = Field(
    default=None, description="Better Stack (Logtail) source token for remote logging"
  )
  logtail_host: Optional[str] = Field(
    default=None, description="Better Stack (Logtail) host URL"
  )
