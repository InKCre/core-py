"""A Cron occurrence and its admitted Job commit together."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from app.engine import AsyncSessionFactory
from app.persistence.job.repository import JobRepository
from app.persistence.job.uow import JobUnitOfWork
from app.persistence.source.repository import SourceRepository
from .repository import CronRepository


@dataclass(frozen=True)
class CronUnitOfWork(JobUnitOfWork):
  crons: CronRepository


@asynccontextmanager
async def cron_uow() -> AsyncGenerator[CronUnitOfWork, None]:
  async with AsyncSessionFactory.begin() as session:
    yield CronUnitOfWork(
      JobRepository(session), SourceRepository(session), CronRepository(session)
    )
