"""Short persistence scope; provider calls run after it closes."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from app.engine import AsyncSessionFactory
from .repository import SemanticRetrievalRepository


@asynccontextmanager
async def semantic_retrieval_uow() -> AsyncGenerator[SemanticRetrievalRepository, None]:
  async with AsyncSessionFactory.begin() as session:
    yield SemanticRetrievalRepository(session)
