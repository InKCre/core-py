"""Source state, graph and storage participate in one short transaction."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from app.engine import AsyncSessionFactory
from app.persistence.info_base.uow import GraphUnitOfWork
from app.persistence.info_base.repository import BlockRepository, RelationRepository
from app.persistence.info_base.storage import StorageRepository
from app.persistence.deployment_config.repository import DeploymentConfigRepository
from .repository import SourceRepository


@dataclass(frozen=True)
class SourceUnitOfWork:
  sources: SourceRepository
  graph: GraphUnitOfWork
  configuration: DeploymentConfigRepository


@asynccontextmanager
async def source_uow() -> AsyncGenerator[SourceUnitOfWork, None]:
  async with AsyncSessionFactory.begin() as session:
    yield SourceUnitOfWork(
      SourceRepository(session),
      GraphUnitOfWork(
        BlockRepository(session), RelationRepository(session), StorageRepository(session)
      ),
      DeploymentConfigRepository(session),
    )
