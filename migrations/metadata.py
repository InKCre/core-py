"""Explicit Alembic metadata registration."""

from sqlalchemy import MetaData

from app.schemas import Base
from libs.obsrv.log_record import LogModel


def get_target_metadata() -> MetaData:
  """Return all application tables expected to participate in migrations."""
  log_table_name = LogModel.__tablename__
  if log_table_name not in Base.metadata.tables:
    raise RuntimeError(f"Migration metadata is missing required table: {log_table_name}")
  return Base.metadata
