"""Task-local async navigation check against the isolated PostgreSQL runtime."""

import asyncio
import uuid

from app.business.graph_navigation_retrieval import GraphNavigationRetrievalManager as Nav
from app.engine import ASYNC_DB_ENGINE
from app.persistence.info_base.uow import graph_uow
from app.schemas.graph_navigation_retrieval import PathFound, PathLimitReached, PathNotFound
from app.schemas.info_base.block import BlockForm


async def main():
  ids = []
  try:
    async with graph_uow() as uow:
      blocks = await uow.blocks.create_many(
        BlockForm(resolver="core.text.v1", content=uuid.uuid4().hex) for _ in range(3)
      )
      ids = [block.id for block in blocks if block.id is not None]
      left, middle, right = ids
      first = await uow.relations.create(left, middle, "probe")
      second = await uow.relations.create(middle, right, "probe")
    path = await Nav.find_path(left, right, direction="out", contents=("probe",))
    assert isinstance(path, PathFound) and path.block_path == (left, middle, right)
    assert isinstance(await Nav.find_path(right, left, direction="out"), PathNotFound)
    assert isinstance(await Nav.find_path(left, right, max_hops=1), PathLimitReached)
    page = await Nav.get_block_neighborhood(middle, limit=1)
    assert page is not None and page.next_cursor == second.id
    remaining = await Nav.get_block_neighborhood(middle, limit=1, cursor=page.next_cursor)
    assert remaining is not None and remaining.graph.relations[0].id == first.id
    assert first.id is not None
    relation = await Nav.get_relation_neighborhood(first.id)
    assert relation is not None and {block.id for block in relation.graph.blocks} == {
      left,
      middle,
    }
    print("navigation direction, hop limit, cursor, endpoint closure: passed")
  finally:
    async with graph_uow() as uow:
      for block_id in ids:
        await uow.blocks.delete(block_id)
    await ASYNC_DB_ENGINE.dispose()


if __name__ == "__main__":
  asyncio.run(main())
