__all__ = [
    "SQLDB_ENGINE",
    "get_db_session",
    "SessionLocal",
]

import os
import typing
import sqlmodel


# configs
DB_CONN_STRING = os.getenv("DB_CONN_STRING", "")


SQLDB_ENGINE = sqlmodel.create_engine(url=DB_CONN_STRING, pool_pre_ping=True)


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
