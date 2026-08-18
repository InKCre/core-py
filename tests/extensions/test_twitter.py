import asyncio
import json
from pathlib import Path
import subprocess
import sys
import typing
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from app.business.extension.runtime import ExtensionRuntimeRecord, PublicHTTPRouteClaim
from app.business.peer import PeerManager
from app.business.source import SourceManager
from app.schemas.job import JobModel
from app.schemas.peer import CorePeerConfig
from extensions.twitter import Extension, TwitterExtensionConfig
from extensions.twitter.api import OfficialAPI, TwikitAPI, TwitterAPI
import extensions.twitter.bookmark as bookmark
from extensions.twitter.bookmark import CollectConfig, Source as BookmarkSource
import extensions.twitter.setup_flow as setup
from extensions.twitter.setup_flow import (
  SaveOAuthAppRequest,
  TwitterAccount,
  TwitterExtensionState,
  TwitterSetupConflict,
)

from tests.extensions.runtime_support import publish_extension


COOKIE_CONVERTER = (
  Path(__file__).resolve().parents[2]
  / "extensions"
  / "twitter"
  / "scripts"
  / "cookie-string-to-json.py"
)


@pytest.fixture(autouse=True)
def clean_twitter_runtime():
  TwitterAPI.SINGLETON = None
  Extension.unpublish()
  Extension.release_runtime()
  yield
  TwitterAPI.SINGLETON = None
  Extension.unpublish()
  Extension.release_runtime()


def attach_runtime(
  config: TwitterExtensionConfig | None = None,
  state: TwitterExtensionState | None = None,
):
  config_box = (config or TwitterExtensionConfig()).model_dump(mode="json")
  state_box = (state or TwitterExtensionState()).model_dump(mode="json")

  def read_config():
    return dict(config_box)

  def persist_config(value):
    config_box.clear()
    config_box.update(value)

  def read_state():
    return dict(state_box)

  def mutate_state(transform):
    updated = transform(dict(state_box))
    state_box.clear()
    state_box.update(updated)
    return dict(state_box)

  def mutate_config_and_state(transform):
    updated_config, updated_state = transform(dict(config_box), dict(state_box))
    config_box.clear()
    config_box.update(updated_config)
    state_box.clear()
    state_box.update(updated_state)
    return dict(config_box), dict(state_box)

  record = ExtensionRuntimeRecord(
    extension_id="twitter",
    config=dict(config_box),
    read_config=read_config,
    persist_config=persist_config,
    read_state=read_state,
    mutate_state=mutate_state,
    mutate_config_and_state=mutate_config_and_state,
    persist_config_schema=lambda _schema: None,
  )
  setattr(Extension, "__runtime_record__", record)
  setattr(Extension, "config", TwitterExtensionConfig.model_validate(config_box))
  return config_box, state_box


def configure_peer_base(monkeypatch, origin: str = "https://core.example") -> None:
  monkeypatch.setattr(
    PeerManager,
    "get_current_config",
    lambda: CorePeerConfig(http_public_base_url=origin),
  )


def connected_state(authorization_id: str = "authorization-1") -> TwitterExtensionState:
  config = TwitterExtensionConfig(client_id="test-client", client_secret="test-secret")
  return TwitterExtensionState(
    account=TwitterAccount(
      token={"access_token": "secret"},
      user_id="42",
      handle="inkcre",
      scopes=("bookmark.read",),
      app_fingerprint=setup._fingerprint(config),
      authorization_id=authorization_id,
      connected_at=setup._now(),
    )
  )


def test_begin_oauth_uses_peer_callback_pkce_s256_and_read_scopes(monkeypatch):
  configure_peer_base(monkeypatch)
  _, state = attach_runtime(
    TwitterExtensionConfig(client_id="test-client", client_secret="test-secret")
  )

  transaction = setup.begin_oauth()
  parsed = urlparse(typing.cast(str, transaction.authorize_url))
  query = parse_qs(parsed.query)

  assert (parsed.scheme, parsed.netloc, parsed.path) == (
    "https",
    "x.com",
    "/i/oauth2/authorize",
  )
  assert query["client_id"] == ["test-client"]
  assert query["redirect_uri"] == ["https://core.example/twitter/auth/callback"]
  assert query["code_challenge_method"] == ["S256"]
  assert set(query["scope"][0].split()) == set(setup.SCOPES)
  assert "bookmark.write" not in query["scope"][0]
  stored = TwitterExtensionState.model_validate(state)
  assert stored.oauth_transactions[transaction.id].pkce_verifier


def test_new_oauth_supersedes_and_scrubs_the_previous_transaction(monkeypatch):
  configure_peer_base(monkeypatch)
  _, state = attach_runtime(
    TwitterExtensionConfig(client_id="test-client", client_secret="test-secret")
  )

  first = setup.begin_oauth()
  setup.begin_oauth()
  prior = TwitterExtensionState.model_validate(state).oauth_transactions[first.id]

  assert prior.status == "expired"
  assert prior.provider_state is None
  assert prior.pkce_verifier is None


def test_replacing_oauth_app_requires_explicit_account_reset_confirmation(monkeypatch):
  configure_peer_base(monkeypatch)
  config, state = attach_runtime(
    TwitterExtensionConfig(client_id="first-client", client_secret="first-secret"),
    connected_state(),
  )

  with pytest.raises(TwitterSetupConflict, match="requires confirmation"):
    setup.save_oauth_app(
      SaveOAuthAppRequest(
        client_id="next-client",
        client_secret="next-secret",
      )
    )

  assert config["client_id"] == "first-client"
  assert TwitterExtensionState.model_validate(state).account is not None

  status = setup.save_oauth_app(
    SaveOAuthAppRequest(
      client_id="next-client",
      client_secret="next-secret",
      confirm_account_reset=True,
    )
  )

  assert config["client_id"] == "next-client"
  assert TwitterExtensionState.model_validate(state).account is None
  assert status.callback_url == "https://core.example/twitter/auth/callback"


def test_direct_oauth_config_change_reconciles_state_before_setup(monkeypatch):
  stale = connected_state()
  _, state = attach_runtime(
    TwitterExtensionConfig(client_id="next-client", client_secret="next-secret"),
    stale,
  )
  reconciled = setup._reconcile_oauth_state()

  assert reconciled.account is None
  assert TwitterExtensionState.model_validate(state).account is None


def test_callback_persists_account_and_scrubs_provider_transaction(monkeypatch):
  configure_peer_base(monkeypatch)
  _, state = attach_runtime(
    TwitterExtensionConfig(client_id="test-client", client_secret="test-secret")
  )
  transaction = setup.begin_oauth()
  stored = TwitterExtensionState.model_validate(state).oauth_transactions[transaction.id]

  async def exchange(config, claimed, code):
    assert code == "authorization-code"
    assert claimed.provider_state == stored.provider_state
    return {"access_token": "secret", "scope": "tweet.read users.read"}, "42", "inkcre"

  monkeypatch.setattr(setup, "_exchange_code", exchange)
  response = asyncio.run(
    setup.oauth_callback(code="authorization-code", state=stored.provider_state)
  )
  finished = TwitterExtensionState.model_validate(state)

  assert response.status_code == 200
  assert finished.account is not None
  assert finished.account.user_id == "42"
  assert finished.account.authorization_id
  terminal = finished.oauth_transactions[transaction.id]
  assert terminal.status == "succeeded"
  assert terminal.provider_state is None
  assert terminal.pkce_verifier is None


def test_provider_denial_does_not_reflect_the_callback_description(monkeypatch):
  configure_peer_base(monkeypatch)
  _, state = attach_runtime(
    TwitterExtensionConfig(client_id="test-client", client_secret="test-secret")
  )
  transaction = setup.begin_oauth()
  stored = TwitterExtensionState.model_validate(state).oauth_transactions[transaction.id]

  response = asyncio.run(
    setup.oauth_callback(
      state=stored.provider_state,
      error="access_denied",
      error_description="provider body that must not be reflected",
    )
  )
  terminal = TwitterExtensionState.model_validate(state).oauth_transactions[transaction.id]

  assert response.status_code == 400
  assert "provider body" not in bytes(response.body).decode()
  assert terminal.error == "Twitter authorization was declined"


@pytest.mark.parametrize(
  ("status_code", "expected"),
  [
    (401, "Twitter current-user lookup failed (HTTP 401)"),
    (
      402,
      "Twitter current-user lookup requires X API credits or project access (HTTP 402)",
    ),
    (403, "Twitter current-user lookup failed (HTTP 403)"),
    (429, "Twitter current-user lookup failed (HTTP 429)"),
    (503, "Twitter current-user lookup failed (HTTP 503)"),
  ],
)
def test_exchange_code_reports_safe_current_user_http_status(
  monkeypatch,
  status_code,
  expected,
):
  class ProviderClient:
    async def fetch_token(self, *args, **kwargs):
      return {"access_token": "provider-token"}

    async def get(self, url):
      return httpx.Response(
        status_code,
        json={"secret_provider_detail": "must not escape"},
        request=httpx.Request("GET", url),
      )

    async def aclose(self):
      return None

  monkeypatch.setattr(setup, "AsyncOAuth2Client", lambda *args, **kwargs: ProviderClient())

  with pytest.raises(setup.TwitterProviderError) as failure:
    asyncio.run(
      setup._exchange_code(
        TwitterExtensionConfig(client_id="test-client", client_secret="test-secret"),
        setup.OAuthTransaction(
          status="pending",
          provider_state="provider-state",
          pkce_verifier="pkce-verifier",
          app_fingerprint="app-fingerprint",
          redirect_uri="https://core.example/twitter/auth/callback",
          created_at=setup._now(),
          expires_at=setup._now() + setup.TRANSACTION_LIFETIME,
        ),
        "authorization-code",
      )
    )

  assert str(failure.value) == expected
  assert "secret_provider_detail" not in str(failure.value)


def test_exchange_code_distinguishes_token_transport_failure(monkeypatch):
  class ProviderClient:
    async def fetch_token(self, *args, **kwargs):
      raise httpx.ConnectError(
        "sensitive transport detail",
        request=httpx.Request("POST", setup.TOKEN_URL),
      )

    async def aclose(self):
      return None

  monkeypatch.setattr(setup, "AsyncOAuth2Client", lambda *args, **kwargs: ProviderClient())

  with pytest.raises(
    setup.TwitterProviderError,
    match="^Twitter token exchange request failed$",
  ):
    asyncio.run(
      setup._exchange_code(
        TwitterExtensionConfig(client_id="test-client", client_secret="test-secret"),
        setup.OAuthTransaction(
          status="pending",
          provider_state="provider-state",
          pkce_verifier="pkce-verifier",
          app_fingerprint="app-fingerprint",
          redirect_uri="https://core.example/twitter/auth/callback",
          created_at=setup._now(),
          expires_at=setup._now() + setup.TRANSACTION_LIFETIME,
        ),
        "authorization-code",
      )
    )


def test_provider_access_fails_before_network_when_authorization_changed(monkeypatch):
  _, state = attach_runtime(
    TwitterExtensionConfig(client_id="test-client", client_secret="test-secret"),
    connected_state(),
  )
  api = OfficialAPI.from_extension(expected_authorization_id="authorization-1")
  state.clear()
  state.update(TwitterExtensionState().model_dump(mode="json"))

  monkeypatch.setattr(
    "extensions.twitter.api.AsyncOAuth2Client",
    lambda *args, **kwargs: pytest.fail("provider client must not be constructed"),
  )
  with pytest.raises(TwitterSetupConflict, match="changed before provider access"):
    asyncio.run(api.get_user())


def test_stale_refresh_cannot_replace_a_newer_token(monkeypatch):
  _, state = attach_runtime(
    TwitterExtensionConfig(client_id="test-client", client_secret="test-secret"),
    connected_state(),
  )
  api = OfficialAPI.from_extension(expected_authorization_id="authorization-1")

  class RefreshingClient:
    def __init__(self, *args, update_token, **kwargs):
      self.update_token = update_token

    async def request(self, *args, **kwargs):
      state["account"]["token"] = {"access_token": "newer-token"}
      await self.update_token({"access_token": "stale-token"})
      raise AssertionError("stale refresh must fail before provider response handling")

    async def aclose(self):
      return None

  monkeypatch.setattr("extensions.twitter.api.AsyncOAuth2Client", RefreshingClient)

  with pytest.raises(TwitterSetupConflict, match="token changed during refresh"):
    asyncio.run(api._request("GET", "/users/me"))
  assert state["account"]["token"] == {"access_token": "newer-token"}


def test_current_provider_unauthorized_response_requires_reconnect(monkeypatch):
  _, state = attach_runtime(
    TwitterExtensionConfig(client_id="test-client", client_secret="test-secret"),
    connected_state(),
  )
  api = OfficialAPI.from_extension(expected_authorization_id="authorization-1")

  class UnauthorizedClient:
    def __init__(self, *args, **kwargs):
      pass

    async def request(self, method, url, **kwargs):
      return httpx.Response(401, request=httpx.Request(method, url))

    async def aclose(self):
      return None

  monkeypatch.setattr("extensions.twitter.api.AsyncOAuth2Client", UnauthorizedClient)

  with pytest.raises(RuntimeError, match="requires reconnection"):
    asyncio.run(api._request("GET", "/users/me"))
  assert state["account"]["reconnect_required"] is True


def test_provider_request_resumes_after_rate_limit_without_request_record(monkeypatch):
  attach_runtime(
    TwitterExtensionConfig(client_id="test-client", client_secret="test-secret"),
    connected_state(),
  )
  api = OfficialAPI.from_extension(expected_authorization_id="authorization-1")
  api.rate_limit_reset["/users/me"] = 0

  class SuccessfulClient:
    def __init__(self, *args, **kwargs):
      pass

    async def request(self, method, url, **kwargs):
      return httpx.Response(
        200,
        json={"data": {"id": "42", "username": "inkcre"}},
        request=httpx.Request(method, url),
      )

    async def aclose(self):
      return None

  monkeypatch.setattr("extensions.twitter.api.AsyncOAuth2Client", SuccessfulClient)

  assert asyncio.run(api._request("GET", "/users/me"))["data"]["id"] == "42"
  assert "/users/me" not in api.rate_limit_reset


class _EmptySession:
  def __enter__(self):
    return self

  def __exit__(self, *args):
    return None

  def commit(self):
    return None


def test_bookmark_collection_uses_current_extension_authorization(monkeypatch):
  captured: list[str | None] = []

  class API:
    async def get_bookmarks(self, **kwargs):
      return type("Result", (), {"tweets": (), "next_page": None})()

  monkeypatch.setattr(
    TwitterAPI,
    "new",
    lambda *, expected_authorization_id=None: (
      captured.append(expected_authorization_id) or API()
    ),
  )
  monkeypatch.setattr(bookmark, "SessionLocal", lambda: _EmptySession())
  job = JobModel(type="source.collect.v1", parameters={}, timeout_seconds=60)

  asyncio.run(
    BookmarkSource(_id=1).collect(
      job,
      CollectConfig(full=True),
    )
  )

  assert captured == [None]


def test_twitter_public_callback_and_setup_capability_follow_publication(monkeypatch):
  monkeypatch.setattr(SourceManager, "sync_source_types", lambda _types: None)
  published = publish_extension(Extension)
  try:
    assert published.client.get("/twitter/setup").status_code == 401
    assert published.client.get("/twitter/auth/callback").status_code == 400
    assert PublicHTTPRouteClaim.permits("GET", "/twitter/auth/callback")
    assert set(published.app.openapi()["paths"]) >= {
      "/twitter/setup",
      "/twitter/setup/oauth-app",
      "/twitter/setup/oauth-transactions",
      "/twitter/setup/oauth-transaction",
      "/twitter/setup/account",
      "/twitter/auth/callback",
    }
    assert [(item.method, item.path) for item in Extension.public_http_routes()] == [
      ("GET", "/auth/callback")
    ]
    assert [item.capability for item in Extension.peer_inbounds()] == [
      setup.TWITTER_SETUP_STATUS_CAPABILITY,
      setup.TWITTER_OAUTH_APP_CONFIGURE_CAPABILITY,
      setup.TWITTER_OAUTH_BEGIN_CAPABILITY,
      setup.TWITTER_OAUTH_TRANSACTION_READ_CAPABILITY,
      setup.TWITTER_OAUTH_DISCONNECT_CAPABILITY,
    ]
  finally:
    published.unpublish()

  assert not PublicHTTPRouteClaim.permits("GET", "/twitter/auth/callback")


def test_on_close_does_not_write_a_stale_config_snapshot(monkeypatch):
  config, _ = attach_runtime(TwitterExtensionConfig(api_language="zh-CN"))

  async def fail_close():
    raise RuntimeError("Twitter cleanup failed")

  monkeypatch.setattr(TwitterAPI, "close_singleton", fail_close)
  with pytest.raises(RuntimeError, match="Twitter cleanup failed"):
    asyncio.run(Extension.on_close())

  assert config == TwitterExtensionConfig(api_language="zh-CN").model_dump(mode="json")


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
