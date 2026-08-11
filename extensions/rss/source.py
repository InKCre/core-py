"""Shared source behavior used by the durable RSS and Atom type wrappers."""

from __future__ import annotations

import typing
import pydantic

from app.business.source import SourceBase
from app.schemas.job import JobModel

from .schema import FeedCollectJobConfig, FeedFamily, FeedSourceConfig
from .service import FeedCollectionService, validate_source_state


class FeedSourceMixin:
  """Thin protocol wrapper behavior; concrete modules preserve source type identity."""

  expected_family: FeedFamily

  async def collect(self, job: JobModel, config: pydantic.BaseModel) -> None:
    source = typing.cast(SourceBase[FeedSourceConfig], self)
    collect_config = FeedCollectJobConfig.model_validate(config)
    service = FeedCollectionService(source._id, self.expected_family)
    state = await service.collect(
      source.get_config(),
      validate_source_state(source.get_state()),
      job,
      collect_config,
    )
    source.set_state(state.model_dump(mode="json"))


__all__ = ["FeedSourceMixin"]
