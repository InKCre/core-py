"""Short lexical database scope, separate from Resolver projection."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from app.engine import AsyncSessionFactory
from .repository import LexicalRepository


@asynccontextmanager
async def lexical_uow() -> AsyncGenerator[LexicalRepository, None]:
  async with AsyncSessionFactory.begin() as session:
    yield LexicalRepository(session)
