"""Deployment configuration transaction composition."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from app.engine import AsyncSessionFactory
from .deployment_config_persistence import DeploymentConfigRepository


@asynccontextmanager
async def configuration_transaction() -> AsyncGenerator[DeploymentConfigRepository, None]:
  async with AsyncSessionFactory.begin() as session:
    yield DeploymentConfigRepository(session)
