"""Explicit Alembic metadata registration."""

from sqlalchemy import MetaData

from app.database_contract import PROTOCOL_SCHEMA
from app.schemas import Base
from libs.obsrv.log_record import LogModel


_qualified_log_table = f"{PROTOCOL_SCHEMA}.{LogModel.__tablename__}"
if _qualified_log_table not in Base.metadata.tables:
  LogModel.__table__.to_metadata(Base.metadata)  # type: ignore[attr-defined]


def get_target_metadata() -> MetaData:
  """Return all application tables expected to participate in migrations."""
  if _qualified_log_table not in Base.metadata.tables:
    raise RuntimeError(
      f"Migration metadata is missing required table: {LogModel.__tablename__}"
    )
  return Base.metadata
