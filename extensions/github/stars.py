"""GitHub Stars and Lists Source orchestration."""

from __future__ import annotations

import pydantic

from app.business.source import SourceBase
from app.engine import SessionLocal
from app.schemas.job import JobModel

from .adapter import GitHubGraphQLAdapter
from .repository import GitHubGraphRepository
from .schema import GitHubSourceConfig


class Source(SourceBase[GitHubSourceConfig], config_cls=GitHubSourceConfig):
  """Synchronize the authenticated GitHub Account's Stars and Lists."""

  async def collect(self, job: JobModel, config: pydantic.BaseModel) -> None:
    del config
    source_config = self.get_config()
    async with GitHubGraphQLAdapter(source_config.github_token) as adapter:
      snapshot = await adapter.fetch_snapshot()

    with SessionLocal() as db_session:
      report = GitHubGraphRepository(db_session).reconcile(self._id, snapshot)
      db_session.commit()
    job.state = report.model_dump(mode="json")


__all__ = ["Source"]
