"""Short Sink persistence scope; runtime start/close happen after commit."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from app.engine import AsyncSessionFactory
from .repository import SinkRepository


@asynccontextmanager
async def sink_uow() -> AsyncGenerator[SinkRepository, None]:
  async with AsyncSessionFactory.begin() as session:
    yield SinkRepository(session)
