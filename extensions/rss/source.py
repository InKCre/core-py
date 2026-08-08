"""Shared source behavior used by the durable RSS and Atom type wrappers."""

from __future__ import annotations

import typing

from app.business.source import SourceBase
from app.schemas.info_base.block import BlockID
from app.schemas.source import SourceCollectJobModel

from .schema import FeedFamily, FeedSourceConfig
from .service import FeedCollectionService, validate_source_state


class FeedSourceMixin:
  """Thin protocol wrapper behavior; concrete modules preserve source type identity."""

  expected_family: FeedFamily

  async def collect(self, job: SourceCollectJobModel) -> None:
    source = typing.cast(SourceBase[FeedSourceConfig], self)
    service = FeedCollectionService(source._id, self.expected_family)
    state = await service.collect(
      source.get_config(),
      validate_source_state(source.get_state()),
      job,
    )
    source.set_state(state.model_dump(mode="json"))

  async def _organize(self, block_id: BlockID) -> None:
    del block_id


__all__ = ["FeedSourceMixin"]
