"""Short transaction for persisted Agent definitions."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from app.engine import AsyncSessionFactory
from .repository import AgentRepository


@asynccontextmanager
async def agent_uow() -> AsyncGenerator[AgentRepository, None]:
  async with AsyncSessionFactory.begin() as session:
    yield AgentRepository(session)
