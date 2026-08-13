"""Black-box HTTP byte hydration through a real local server."""

import asyncio

from aiohttp import web

from app.business.info_base.storage import (
  HTTPStorage,
  StorageContentTooLargeError,
)
from app.schemas.info_base.storage import StorageModel
import pytest


def _storage(max_response_bytes: int) -> HTTPStorage:
  return HTTPStorage(
    StorageModel(
      id=-1,
      type="http",
      nickname="HTTP",
      config={"max_response_bytes": max_response_bytes},
    )
  )


async def _serve_and_hydrate(payload: bytes, limit: int) -> bytes:
  app = web.Application()

  async def content(_request: web.Request) -> web.Response:
    return web.Response(body=payload)

  app.router.add_get("/content", content)
  runner = web.AppRunner(app)
  await runner.setup()
  site = web.TCPSite(runner, "127.0.0.1", 0)
  await site.start()
  try:
    sockets = site._server.sockets  # type: ignore[union-attr]
    port = sockets[0].getsockname()[1]
    return await _storage(limit).get_raw_content(f"http://127.0.0.1:{port}/content")
  finally:
    await runner.cleanup()


def test_http_storage_returns_response_bytes():
  assert asyncio.run(_serve_and_hydrate(b"opaque", 6)) == b"opaque"


def test_http_storage_rejects_response_over_the_configured_limit():
  with pytest.raises(StorageContentTooLargeError):
    asyncio.run(_serve_and_hydrate(b"too-large", 4))


def test_http_storage_rejects_non_http_pointer():
  with pytest.raises(ValueError, match="http:// or https://"):
    asyncio.run(_storage(10).get_raw_content("file:///tmp/content"))
