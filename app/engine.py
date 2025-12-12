__all__ = [
    "SQLDB_ENGINE",
    "get_db_session",
    "SessionLocal",
    "get_database_url",
]

import typing
import sqlmodel
from app.settings import settings


def get_database_url() -> str:
    """
    Get database URL from settings.

    This function is kept for backward compatibility but now delegates
    to the settings module which handles the postgres:// to postgresql://
    conversion via a pydantic validator.

    Returns:
        Database connection URL string
    """
    return settings.database_url


# configs
DATABASE_URL = get_database_url()
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

# Create engine
SQLDB_ENGINE = sqlmodel.create_engine(url=DATABASE_URL, pool_pre_ping=settings.database_scale_0)


def SessionLocal():
    return sqlmodel.Session(SQLDB_ENGINE)


def get_db_session() -> typing.Generator:
    """A fastapi dependency to get a database session."""
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
