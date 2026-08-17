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
from app.schemas.cron import CronModel
from app.schemas.job import JobModel
from app.schemas.peer import CorePeerConfig
from app.schemas.source import SourceModel
from extensions.twitter import Extension, TwitterExtensionConfig
from extensions.twitter.api import OfficialAPI, TwikitAPI, TwitterAPI
import extensions.twitter.bookmark as bookmark
from extensions.twitter.bookmark import CollectConfig, Source as BookmarkSource
import extensions.twitter.setup_flow as setup
from extensions.twitter.setup_flow import (
  SaveOAuthAppCommand,
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
  monkeypatch.setattr(
    setup,
    "_bookmark_source_status",
    lambda state: (state.bookmark_source_id, None, (), setup.SetupCollectAt(), False),
  )
  config, state = attach_runtime(
    TwitterExtensionConfig(client_id="first-client", client_secret="first-secret"),
    connected_state().model_copy(update={"bookmark_cron_id": 9}),
  )
  disabled: list[int | None] = []
  monkeypatch.setattr(
    setup,
    "_disable_bookmark_schedule",
    lambda current: disabled.append(current.bookmark_cron_id),
  )

  with pytest.raises(TwitterSetupConflict, match="requires confirmation"):
    setup.save_oauth_app(
      SaveOAuthAppCommand(
        action="save_oauth_app",
        client_id="next-client",
        client_secret="next-secret",
      )
    )

  assert config["client_id"] == "first-client"
  assert TwitterExtensionState.model_validate(state).account is not None

  status = setup.save_oauth_app(
    SaveOAuthAppCommand(
      action="save_oauth_app",
      client_id="next-client",
      client_secret="next-secret",
      confirm_account_reset=True,
    )
  )

  assert config["client_id"] == "next-client"
  assert TwitterExtensionState.model_validate(state).account is None
  assert disabled == [9]
  assert status.callback_url == "https://core.example/twitter/auth/callback"


def test_direct_oauth_config_change_reconciles_state_before_setup(monkeypatch):
  stale = connected_state().model_copy(update={"bookmark_cron_id": 9})
  _, state = attach_runtime(
    TwitterExtensionConfig(client_id="next-client", client_secret="next-secret"),
    stale,
  )
  disabled: list[int | None] = []
  monkeypatch.setattr(
    setup,
    "_disable_bookmark_schedule",
    lambda current: disabled.append(current.bookmark_cron_id),
  )

  reconciled = setup._reconcile_oauth_state()

  assert reconciled.account is None
  assert TwitterExtensionState.model_validate(state).account is None
  assert disabled == [9]


def test_disconnect_stops_bookmark_collection_before_clearing_account(monkeypatch):
  initial = connected_state().model_copy(update={"bookmark_cron_id": 9})
  _, state = attach_runtime(
    TwitterExtensionConfig(client_id="test-client", client_secret="test-secret"),
    initial,
  )
  disabled: list[int | None] = []
  monkeypatch.setattr(
    setup,
    "_disable_bookmark_schedule",
    lambda current: disabled.append(current.bookmark_cron_id),
  )
  monkeypatch.setattr(setup, "get_setup_status", lambda: None)

  setup.disconnect_account()

  assert disabled == [9]
  assert TwitterExtensionState.model_validate(state).account is None


def test_disabling_bookmark_schedule_preserves_its_reusable_template(monkeypatch):
  cron = CronModel(
    id=9,
    schedule="30 6 * * *",
    enabled=True,
    job_type=setup.SOURCE_COLLECT_JOB_TYPE,
    job_parameters=setup._bookmark_job_parameters(25, "authorization-current"),
    job_timeout_seconds=180,
  )

  class Session:
    def __enter__(self):
      return self

    def __exit__(self, *args):
      return None

    def get(self, model, identifier):
      return cron if model is CronModel and identifier == 9 else None

  saved = []
  monkeypatch.setattr(setup, "SessionLocal", Session)
  monkeypatch.setattr(
    setup.CronManager,
    "update",
    lambda cron_id, form: saved.append((form, cron_id)),
  )

  setup._disable_bookmark_schedule(
    connected_state().model_copy(update={"bookmark_cron_id": 9})
  )

  form, cron_id = saved[0]
  assert cron_id == 9
  assert form.enabled is False
  assert form.schedule == "30 6 * * *"
  assert form.job_parameters == cron.job_parameters


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


def test_bookmark_collection_requires_the_scheduled_authorization(monkeypatch):
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
      CollectConfig(
        full=True,
        authorization_id="authorization-current",
      ),
    )
  )

  assert captured == ["authorization-current"]


def test_setup_projects_bookmark_choice_to_source_and_cron_authorities(monkeypatch):
  _, state = attach_runtime(
    TwitterExtensionConfig(client_id="test-client", client_secret="test-secret"),
    connected_state("authorization-current"),
  )
  source = SourceModel(
    id=25,
    type=setup.BOOKMARK_SOURCE_TYPE,
    nickname="Twitter Bookmarks",
    config={},
  )
  captured = []

  monkeypatch.setattr(SourceManager, "create", lambda *args, **kwargs: source)

  def create_cron(form):
    captured.append(("create", form, None))
    return CronModel(id=9, **form.model_dump())

  monkeypatch.setattr(setup.CronManager, "create", create_cron)
  monkeypatch.setattr(
    setup,
    "get_setup_status",
    lambda: setup.TwitterSetupStatus(
      backend="official",
      callback_url="https://core.example/twitter/auth/callback",
      oauth_app_configured=True,
      connected=True,
    ),
  )

  setup.configure_bookmark_source(
    setup.ConfigureBookmarkSourceCommand(
      action="configure_bookmark_source",
      collect_at=setup.SetupCollectAt(hour=6, minute=30),
    )
  )

  persisted = TwitterExtensionState.model_validate(state)
  assert persisted.bookmark_source_id == 25
  assert persisted.bookmark_cron_id == 9
  operation, form, previous_id = captured[0]
  assert operation == "create"
  assert previous_id is None
  assert form.schedule == "30 6 * * *"
  assert form.enabled is False
  assert form.job_parameters == {
    "source": 25,
    "config": {
      "full": False,
      "result_limit": 40,
      "authorization_id": "authorization-current",
    },
  }


def test_finish_cannot_commit_readiness_after_account_reconnect(monkeypatch):
  initial = connected_state("authorization-old").model_copy(
    update={"bookmark_source_id": 25, "bookmark_cron_id": 9}
  )
  _, state = attach_runtime(
    TwitterExtensionConfig(client_id="test-client", client_secret="test-secret"),
    initial,
  )
  source = SourceModel(
    id=25,
    type=setup.BOOKMARK_SOURCE_TYPE,
    nickname="Twitter Bookmarks",
    config={},
  )
  cron = CronModel(
    id=9,
    schedule="0 6 * * *",
    enabled=True,
    job_type=setup.SOURCE_COLLECT_JOB_TYPE,
    job_parameters=setup._bookmark_job_parameters(25, "authorization-old"),
  )

  class API:
    async def get_user(self):
      state["account"]["authorization_id"] = "authorization-new"
      return "42", "inkcre"

    async def close(self):
      return None

  class Session:
    def __enter__(self):
      return self

    def __exit__(self, *args):
      return None

    def get(self, model, identifier):
      if model is SourceModel and identifier == 25:
        return source
      if model is CronModel and identifier == 9:
        return cron
      return None

  monkeypatch.setattr(OfficialAPI, "from_extension", lambda **kwargs: API())
  monkeypatch.setattr(setup, "SessionLocal", Session)
  monkeypatch.setattr(
    setup.CronManager,
    "update",
    lambda cron_id, form: CronModel(id=cron_id, **form.model_dump()),
  )
  monkeypatch.setattr(
    setup.CronManager,
    "run_now",
    lambda _cron_id: pytest.fail("stale authorization must not schedule a Job"),
  )

  with pytest.raises(TwitterSetupConflict, match="changed during Finish"):
    asyncio.run(setup.finish_setup())


def test_twitter_public_callback_and_setup_capability_follow_publication(monkeypatch):
  monkeypatch.setattr(SourceManager, "sync_source_types", lambda _types: None)
  published = publish_extension(Extension)
  try:
    assert (
      published.client.post("/twitter/setup", json={"action": "get_status"}).status_code
      == 401
    )
    assert published.client.get("/twitter/auth/callback").status_code == 400
    assert PublicHTTPRouteClaim.permits("GET", "/twitter/auth/callback")
    assert set(published.app.openapi()["paths"]) >= {
      "/twitter/setup",
      "/twitter/auth/callback",
    }
    assert [(item.method, item.path) for item in Extension.public_http_routes()] == [
      ("GET", "/auth/callback")
    ]
    assert [item.capability for item in Extension.peer_inbounds()] == [
      setup.TWITTER_SETUP_CAPABILITY
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
