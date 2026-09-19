"""The process-owned async engine and session factory; lifespan disposes the pool."""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.settings import settings


ASYNC_DB_ENGINE = create_async_engine(
  settings.database_url, pool_pre_ping=settings.database_scale_0
)
AsyncSessionFactory = async_sessionmaker(ASYNC_DB_ENGINE, expire_on_commit=False)

__all__ = ["ASYNC_DB_ENGINE", "AsyncSessionFactory"]
