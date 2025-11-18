__all__ = [
    "SQLDB_ENGINE",
    "get_db_session",
    "SessionLocal",
    "get_database_url",
]

import os
import typing
import sqlmodel


def get_database_url() -> str:
    """
    Get database URL from environment variables.

    Heroku provides DATABASE_URL with 'postgres://' scheme, but SQLAlchemy 2.0+
    requires 'postgresql://' scheme. This function handles the conversion.

    Returns:
        Database connection URL string
    """
    db_url = os.getenv("DATABASE_URL", "")

    # Convert postgres:// to postgresql:// for SQLAlchemy 2.0+ compatibility
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    return db_url


# configs
DATABASE_URL = get_database_url()


# Create engine - use SQLite in-memory database if DATABASE_URL is empty
# to allow importing during tests. In production, DATABASE_URL should always be set
SQLDB_ENGINE = sqlmodel.create_engine(
    url=DATABASE_URL or "sqlite:///:memory:", pool_pre_ping=True
)


# SessionLocal = sqlalchemy.orm.sessionmaker(autocommit=False, autoflush=False, bind=SQLDB_ENGINE)
def SessionLocal():
    return sqlmodel.Session(SQLDB_ENGINE)


def get_db_session() -> typing.Generator:
    """A fastapi dependency to get a database session."""
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
