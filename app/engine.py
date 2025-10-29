__all__ = [
    "SQLDB_ENGINE",
    "get_db_session",
    "SessionLocal",
]

import os
import typing
import sqlmodel


# Detect if running in Cloudflare Workers environment
IS_CLOUDFLARE_WORKER = os.getenv("CF_WORKER", "false").lower() == "true"

# configs
DB_CONN_STRING = os.getenv("DB_CONN_STRING", "")

# Engine configuration
# For Cloudflare Workers with Hyperdrive, connection pooling is handled by Hyperdrive
# so we disable SQLAlchemy's connection pool
if IS_CLOUDFLARE_WORKER:
    # Hyperdrive handles connection pooling
    SQLDB_ENGINE = sqlmodel.create_engine(
        url=DB_CONN_STRING,
        pool_pre_ping=True,
        poolclass=sqlmodel.pool.NullPool,  # Disable connection pooling
    )
else:
    # Traditional deployment with standard connection pooling
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
