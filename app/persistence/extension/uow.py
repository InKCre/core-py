"""Short Extension transaction; publication and acquisition remain outside."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from app.engine import AsyncSessionFactory
from .repository import ExtensionRepository


@asynccontextmanager
async def extension_uow() -> AsyncGenerator[ExtensionRepository, None]:
  async with AsyncSessionFactory.begin() as session:
    yield ExtensionRepository(session)
