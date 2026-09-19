"""Graph transaction composition; repositories share one private session."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from app.engine import AsyncSessionFactory

from .repository import BlockRepository, RelationRepository
from .storage import StorageRepository


@dataclass(frozen=True)
class GraphUnitOfWork:
  blocks: BlockRepository
  relations: RelationRepository
  storage: StorageRepository


@asynccontextmanager
async def graph_uow() -> AsyncGenerator[GraphUnitOfWork, None]:
  """Commit on success; roll back on failure and always close the session."""
  async with AsyncSessionFactory.begin() as session:
    yield GraphUnitOfWork(
      BlockRepository(session), RelationRepository(session), StorageRepository(session)
    )
