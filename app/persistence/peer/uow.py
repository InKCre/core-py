"""Transaction scopes for Peer facts and database-owned leases."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from app.engine import AsyncSessionFactory
from .repository import PeerRepository


@asynccontextmanager
async def peer_uow() -> AsyncGenerator[PeerRepository, None]:
  async with AsyncSessionFactory.begin() as session:
    yield PeerRepository(session)
