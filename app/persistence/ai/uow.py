"""Short database scope for AI facts; provider calls outlive this scope."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from app.engine import AsyncSessionFactory
from .repository import AIRepository


@asynccontextmanager
async def ai_uow() -> AsyncGenerator[AIRepository, None]:
  async with AsyncSessionFactory.begin() as session:
    yield AIRepository(session)
