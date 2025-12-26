"""PostgreSQL logging handler."""

import logging
import sqlmodel
from typing import Optional as Opt
from app.settings import settings
from libs.obsrv.log_record import ENABLE_LOG_BACKEND, adapt_log_record


class PostgreSQLHandler(logging.Handler):
  """Logging handler that writes logs to PostgreSQL database."""

  def __init__(
    self,
    dsn: str,
    table: str = "logs",
    level: Opt[int] = None,
  ):
    if level is None:
      level = settings.obsrv.logging_backend_level
    super().__init__(level)
    self.dsn = dsn
    self.table = table
    self.engine = sqlmodel.create_engine(dsn, pool_size=2, max_overflow=0)

  def emit(self, record: logging.LogRecord) -> None:
    """Emit a log record to PostgreSQL."""
    if not ENABLE_LOG_BACKEND.get():
      return
    log_entry = adapt_log_record(record)
    try:
      with sqlmodel.Session(self.engine) as session:
        session.add(log_entry)
        session.commit()
    except Exception as e:
      # If logging to DB fails, we don't want to recurse
      print(f"Failed to log to PostgreSQL: {e}")

  def close(self) -> None:
    """Close the database engine."""
    if self.engine:
      self.engine.dispose()
    super().close()
