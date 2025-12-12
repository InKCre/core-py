__all__ = [
    "SQLDB_ENGINE",
    "get_db_session",
    "SessionLocal",
]

import typing
import sqlmodel
from app.settings import settings


# configs
DATABASE_URL = settings.database_url

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
