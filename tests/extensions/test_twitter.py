import asyncio
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import parse_qs, urlparse

import pytest

from app.business.extension.runtime import ExtensionRuntimeRecord
from app.business.source import SourceManager
from extensions.twitter import Extension, TwitterExtensionConfig
from extensions.twitter.api import OfficialAPI, TwikitAPI, TwitterAPI


COOKIE_CONVERTER = (
  Path(__file__).resolve().parents[2]
  / "extensions"
  / "twitter"
  / "scripts"
  / "cookie-string-to-json.py"
)


def test_get_oauth_authorize_url(monkeypatch):
  monkeypatch.setenv("API_BASE_URL", "https://preview.example")
  api = OfficialAPI(client_id="test-client", client_secret="test-secret")

  parsed = urlparse(api.get_oauth_authorize_url())
  query = parse_qs(parsed.query)

  assert parsed.scheme == "https"
  assert parsed.netloc == "x.com"
  assert query["client_id"] == ["test-client"]
  assert query["redirect_uri"] == ["https://preview.example/twitter/auth/callback"]
  assert query["code_challenge_method"] == ["plain"]


def test_cookie_converter_reads_sensitive_input_from_stdin():
  result = subprocess.run(  # noqa: S603
    [sys.executable, str(COOKIE_CONVERTER)],
    input="session=secret; preference=compact",
    check=False,
    capture_output=True,
    text=True,
  )

  assert result.returncode == 0
  assert json.loads(result.stdout) == {
    "session": "secret",
    "preference": "compact",
  }


def test_bookmark_api_creates_the_registered_source_type(monkeypatch):
  import fastapi
  from fastapi.routing import APIRoute

  created: list[tuple[str, str | None]] = []
  monkeypatch.setattr(TwitterAPI, "new", lambda api_router=None: object())
  monkeypatch.setattr(
    SourceManager,
    "create",
    lambda source_type, nickname=None: created.append((source_type, nickname)),
  )
  router = fastapi.APIRouter()
  Extension._register_apis(router)
  route = next(
    route
    for route in router.routes
    if isinstance(route, APIRoute) and route.path == "/bookmark"
  )

  route.endpoint("Reading")
  assert created == [("extensions.twitter.bookmark.Source", "Reading")]


def test_on_close_persists_config_even_when_api_cleanup_fails(monkeypatch):
  persisted: list[dict[str, object]] = []
  record = ExtensionRuntimeRecord(
    extension_id="twitter",
    config={},
    persist_config=persisted.append,
    persist_config_schema=lambda schema: None,
  )
  setattr(Extension, "__runtime_record__", record)
  setattr(Extension, "config", TwitterExtensionConfig(api_language="zh-CN"))

  async def fail_close():
    raise RuntimeError("Twitter cleanup failed")

  monkeypatch.setattr(TwitterAPI, "close_singleton", fail_close)
  try:
    with pytest.raises(RuntimeError, match="Twitter cleanup failed"):
      asyncio.run(Extension.on_close())
  finally:
    Extension.release_runtime()

  assert persisted == [TwitterExtensionConfig(api_language="zh-CN").model_dump()]


def test_twikit_cookie_persistence_creates_runtime_directory(monkeypatch, tmp_path):
  cookie_path = tmp_path / "runtime/twitter/twikit_cookies.json"
  monkeypatch.setattr(TwikitAPI, "DATA_DIRECTORY", cookie_path.parent)
  monkeypatch.setattr(TwikitAPI, "COOKIES_FILE", cookie_path)
  saved: list[str] = []
  api = object.__new__(TwikitAPI)
  api._client = type(
    "FakeClient",
    (),
    {"save_cookies": lambda self, path: saved.append(path)},
  )()

  asyncio.run(api.close())

  assert cookie_path.parent.is_dir()
  assert saved == [str(cookie_path)]
