"""Task-scoped Telegram and Twitter graph/checkpoint atomicity."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import uuid

from app.business.info_base.resolver import register_core_resolvers
from app.business.source import SourceManager
from app.engine import ASYNC_DB_ENGINE
from app.persistence.source.repository import SourceRepository
from app.persistence.source.uow import source_uow
from app.schemas.info_base.block import BlockForm
from app.schemas.job import JobModel
from extensions.telegram.source import Source as TelegramSource
from extensions.twitter.bookmark import Source as TwitterSource, CollectConfig
from extensions.twitter.api import TwitterAPI


async def exercise():
  register_core_resolvers()
  key = uuid.uuid4().hex
  tweet_id = int(key[:15], 16)
  await SourceManager.sync_source_types_async()
  telegram = await SourceManager.create(
    f"{TelegramSource.__module__}.{TelegramSource.__qualname__}",
    config={"bot_token": "probe", "bound_user_id": 1},
  )
  twitter = await SourceManager.create(
    f"{TwitterSource.__module__}.{TwitterSource.__qualname__}",
    config={},
  )
  assert telegram.id is not None and twitter.id is not None
  original = SourceRepository.save

  async def fail(self, source):
    await original(self, source)
    raise RuntimeError("injected checkpoint failure")

  try:
    tg = TelegramSource(telegram.id)
    await tg._pin_bot(1)
    with patch.object(SourceRepository, "save", fail):
      try:
        await tg._persist_update(1, text=BlockForm(content=key, resolver="core.text.v1"))
      except RuntimeError:
        pass
      else:
        raise AssertionError("expected checkpoint failure")
    async with source_uow() as uow:
      assert await uow.graph.blocks.find_content("core.text.v1", key) is None
    state = await tg.get_state()
    assert state.get("last_update_id") is None
    results = await asyncio.gather(
      *(
        tg._persist_update(1, text=BlockForm(content=key, resolver="core.text.v1"))
        for _ in range(4)
      )
    )
    assert [r.status for r in results].count("saved") == 1

    tweet = SimpleNamespace(
      id=tweet_id,
      user_id=None,
      conversation_id=None,
      quote=None,
      text=key,
      photos=(),
      videos=(),
      urls=(),
    )
    api = SimpleNamespace(
      get_bookmarks=AsyncMock(return_value=SimpleNamespace(tweets=[tweet], next_page=None))
    )
    tw = TwitterSource(twitter.id)
    job = JobModel(type="core.source.collect.v1", timeout_seconds=30)
    with patch.object(TwitterAPI, "new", AsyncMock(return_value=api)):
      with patch.object(SourceRepository, "save", fail):
        try:
          await tw.collect(job, CollectConfig())
        except RuntimeError:
          pass
        else:
          raise AssertionError("expected checkpoint failure")
      assert (await tw.get_state()).get("latest_tweet_id") is None
      async with source_uow() as uow:
        assert not await uow.graph.blocks.find_json_field(
          "extensions.twitter.tweet.v1", "id", str(tweet_id)
        )
      await tw.collect(job, CollectConfig())
      assert (await tw.get_state())["latest_tweet_id"] == tweet_id
    print("PASS: concurrent Telegram deduplication and atomic producer checkpoints")
  finally:
    async with source_uow() as uow:
      block = await uow.graph.blocks.find_content("core.text.v1", key)
      candidates = list(
        await uow.graph.blocks.find_json_field(
          "extensions.twitter.tweet.v1", "id", str(tweet_id)
        )
      )
      if block is not None:
        candidates.append(block)
      for candidate in candidates:
        if candidate.id is not None:
          await uow.graph.blocks.delete(candidate.id)
      for source_id in (telegram.id, twitter.id):
        source = await uow.sources.get(source_id)
        if source is not None:
          await uow.sources.delete(source)
    await ASYNC_DB_ENGINE.dispose()


if __name__ == "__main__":
  asyncio.run(exercise())
