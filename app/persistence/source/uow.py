"""Source transaction scope."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from app.engine import AsyncSessionFactory
from .repository import SourceRepository


@asynccontextmanager
async def source_uow() -> AsyncGenerator[SourceRepository, None]:
  async with AsyncSessionFactory.begin() as session:
    yield SourceRepository(session)
