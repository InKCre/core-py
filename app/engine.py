__all__ = [
  "SQLDB_ENGINE",
  "get_db_session",
  "SessionLocal",
  "ASYNC_DB_ENGINE",
  "AsyncSessionFactory",
]

import typing
import sqlmodel
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.settings import settings


# configs
DATABASE_URL = settings.database_url

# Create engine
SQLDB_ENGINE = sqlmodel.create_engine(
  url=DATABASE_URL, pool_pre_ping=settings.database_scale_0
)

# The synchronous factory remains only for callers awaiting migration.
# Engine construction does not connect; lifespan owns asynchronous pool disposal.
ASYNC_DB_ENGINE = create_async_engine(DATABASE_URL, pool_pre_ping=settings.database_scale_0)
AsyncSessionFactory = async_sessionmaker(ASYNC_DB_ENGINE, expire_on_commit=False)


def SessionLocal():
  return sqlmodel.Session(SQLDB_ENGINE)


def get_db_session() -> typing.Generator:
  """A fastapi dependency to get a database session."""
  db_session = SessionLocal()
  try:
    yield db_session
  finally:
    db_session.close()
