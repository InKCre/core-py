"""Regression tests for the resolver decomposition protocol."""

import asyncio

import pytest

from app.business.info_base.resolver.image import ImageResolver
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel


def test_image_breakdown_accepts_persisted_items(monkeypatch):
  async def fake_img2text(_resolver):
    return {"summary": "A diagram", "details": []}

  monkeypatch.setattr(
    ImageResolver,
    "_ImageResolver__img2text",
    fake_img2text,
  )
  resolver = ImageResolver(
    BlockModel(
      id=10, resolver="image", content="https://example.test/image.png", storage=-1
    )
  )

  async def exercise_protocol() -> tuple[BlockModel, RelationModel]:
    generator = resolver.breakdown()
    summary_block = await anext(generator)
    assert isinstance(summary_block, BlockModel)
    summary_block.id = 11

    relation = await generator.asend(summary_block)
    assert isinstance(relation, RelationModel)
    with pytest.raises(StopAsyncIteration):
      await generator.asend(relation)
    return summary_block, relation

  summary_block, relation = asyncio.run(exercise_protocol())

  assert summary_block.content == "A diagram"
  assert relation.from_ == 10
  assert relation.to_ == 11
  assert relation.content == "alt:text"
