"""Task-scoped complete GitHub snapshot transaction probe."""

import asyncio
import uuid

from app.business.source import SourceManager
from app.engine import ASYNC_DB_ENGINE
from app.persistence.source.uow import source_uow
from extensions.github.stars import Source
from extensions.github.reconcile import GitHubGraphReconciler, GitHubSourceBindingError
from extensions.github.schema import (
  GitHubAccount,
  GitHubSnapshot,
  GitHubList,
  GitHubListFact,
)


async def exercise():
  key = uuid.uuid4().hex
  await SourceManager.sync_source_types_async()
  source = await SourceManager.create(
    f"{Source.__module__}.{Source.__qualname__}", config={"github_token": "probe"}
  )
  assert source.id is not None
  snapshot = GitHubSnapshot(
    lists=(
      GitHubListFact(
        list=GitHubList(node_id=key + "-list", name="probe", slug="probe", is_private=False)
      ),
    ),
    account=GitHubAccount(
      node_id=key, kind="user", login=key, url="https://example.test/" + key
    ),
  )
  try:
    async with source_uow() as uow:
      first = await GitHubGraphReconciler(uow).reconcile(source.id, snapshot)
    assert first.blocks_created == 2 and first.relations_created == 2
    async with source_uow() as uow:
      second = await GitHubGraphReconciler(uow).reconcile(source.id, snapshot)
    assert second.blocks_created == second.blocks_updated == second.relations_created == 0
    async with source_uow() as uow:
      removed = await GitHubGraphReconciler(uow).reconcile(
        source.id, snapshot.model_copy(update={"lists": ()})
      )
    assert removed.relations_deleted == 1
    try:
      async with source_uow() as uow:
        await GitHubGraphReconciler(uow).reconcile(
          source.id,
          snapshot.model_copy(
            update={"account": snapshot.account.model_copy(update={"node_id": "other"})}
          ),
        )
    except GitHubSourceBindingError:
      pass
    else:
      raise AssertionError("account rebinding accepted")
    stored = await SourceManager.get(source.id)
    assert stored is not None and stored.state["account_node_id"] == key
    print("PASS: snapshot, idempotent replay, account binding rollback")
  finally:
    async with source_uow() as uow:
      stored = await uow.sources.get(source.id)
      if stored is not None:
        if stored.block is not None:
          relations = await uow.graph.relations.get(stored.block, include_in=False)
          for relation in relations:
            await uow.graph.blocks.delete(relation.to_)
          await uow.graph.blocks.delete(stored.block)
        for block in await uow.graph.blocks.find_json_field(
          "extensions.github.list.v1", "node_id", key + "-list"
        ):
          if block.id is not None:
            await uow.graph.blocks.delete(block.id)
        await uow.sources.delete(stored)
    await ASYNC_DB_ENGINE.dispose()


if __name__ == "__main__":
  asyncio.run(exercise())
