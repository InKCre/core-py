"""Whole-Extension setup workflow owned by the Twitter Extension."""

from __future__ import annotations

import base64
import datetime
import hashlib
import html
import secrets
import typing
import uuid

from authlib.integrations.base_client.errors import OAuthError  # pyrefly: ignore[untyped-import]
from authlib.integrations.httpx_client import (  # pyrefly: ignore[untyped-import]
  AsyncOAuth2Client,
  OAuth2Client,
)
import fastapi
from fastapi.responses import HTMLResponse
import httpx
import pydantic
import sqlmodel

from app.business.cron import CronManager
from app.business.job import JobManager
from app.business.peer import PeerHTTPInbound, PeerManager
from app.business.source import SOURCE_COLLECT_JOB_TYPE, SourceManager
from app.engine import SessionLocal
from app.middleware import require_peer_jwt
from app.schemas.cron import CronForm, CronModel
from app.schemas.source import SourceModel


if typing.TYPE_CHECKING:
  from . import TwitterExtensionConfig


TWITTER_SETUP_CAPABILITY = "inkcre.twitter.setup.v1"
TWITTER_SETUP_INBOUND = PeerHTTPInbound(
  capability=TWITTER_SETUP_CAPABILITY,
  method="POST",
  path="/twitter/setup",
)
AUTHORIZE_URL = "https://x.com/i/oauth2/authorize"
TOKEN_URL = "https://api.x.com/2/oauth2/token"  # noqa: S105
CURRENT_USER_URL = "https://api.x.com/2/users/me"
SCOPES = ("tweet.read", "users.read", "bookmark.read", "offline.access")
TRANSACTION_LIFETIME = datetime.timedelta(minutes=10)
TERMINAL_RETENTION = datetime.timedelta(minutes=10)
MAX_TRANSACTIONS = 8
BOOKMARK_SOURCE_TYPE = "extensions.twitter.bookmark.Source"


def _now() -> datetime.datetime:
  return datetime.datetime.now(datetime.UTC)


class TwitterAccount(pydantic.BaseModel):
  token: dict[str, typing.Any]
  user_id: str
  handle: str
  scopes: tuple[str, ...] = ()
  app_fingerprint: str
  authorization_id: str
  connected_at: datetime.datetime
  reconnect_required: bool = False


class OAuthTransaction(pydantic.BaseModel):
  status: typing.Literal["pending", "exchanging", "succeeded", "failed", "expired"]
  provider_state: str | None = None
  pkce_verifier: str | None = None
  app_fingerprint: str
  redirect_uri: str
  created_at: datetime.datetime
  expires_at: datetime.datetime
  closed_at: datetime.datetime | None = None
  error: str | None = None


class TwitterExtensionState(pydantic.BaseModel):
  account: TwitterAccount | None = None
  oauth_transactions: dict[str, OAuthTransaction] = pydantic.Field(default_factory=dict)
  bookmark_source_id: int | None = None
  bookmark_cron_id: int | None = None


class SetupCollectAt(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  day_of_week: int | None = pydantic.Field(default=None, ge=0, le=6)
  hour: int = pydantic.Field(default=0, ge=0, le=23)
  minute: int = pydantic.Field(default=0, ge=0, le=59)

  def cron_schedule(self) -> str:
    day = "*" if self.day_of_week is None else str(self.day_of_week)
    return f"{self.minute} {self.hour} * * {day}"

  @classmethod
  def from_cron_schedule(cls, schedule: str) -> SetupCollectAt | None:
    parts = schedule.split()
    if len(parts) != 5 or parts[2:4] != ["*", "*"]:
      return None
    try:
      return cls(
        minute=int(parts[0]),
        hour=int(parts[1]),
        day_of_week=None if parts[4] == "*" else int(parts[4]),
      )
    except (ValueError, pydantic.ValidationError):
      return None


class BookmarkSourceView(pydantic.BaseModel):
  source_id: int
  nickname: str


class OAuthTransactionView(pydantic.BaseModel):
  id: str
  status: str
  authorize_url: str | None = None
  expires_at: datetime.datetime
  error: str | None = None


class TwitterSetupStatus(pydantic.BaseModel):
  backend: str
  callback_url: str
  oauth_app_configured: bool
  client_id: str | None = None
  connected: bool
  user_id: str | None = None
  handle: str | None = None
  scopes: tuple[str, ...] = ()
  reconnect_required: bool = False
  bookmark_source_id: int | None = None
  bookmark_cron_id: int | None = None
  bookmark_sources: tuple[BookmarkSourceView, ...] = ()
  collect_at: SetupCollectAt = pydantic.Field(default_factory=SetupCollectAt)
  bookmark_source_ready: bool = False
  ready: bool = False


class GetStatusCommand(pydantic.BaseModel):
  action: typing.Literal["get_status"]


class SaveOAuthAppCommand(pydantic.BaseModel):
  action: typing.Literal["save_oauth_app"]
  client_id: str = pydantic.Field(min_length=1, max_length=256)
  client_secret: str = pydantic.Field(min_length=1, max_length=1024)
  confirm_account_reset: bool = False


class BeginOAuthCommand(pydantic.BaseModel):
  action: typing.Literal["begin_oauth"]


class GetOAuthTransactionCommand(pydantic.BaseModel):
  action: typing.Literal["get_oauth_transaction"]
  transaction_id: str


class DisconnectAccountCommand(pydantic.BaseModel):
  action: typing.Literal["disconnect_account"]


class ConfigureBookmarkSourceCommand(pydantic.BaseModel):
  action: typing.Literal["configure_bookmark_source"]
  source_id: int | None = None
  nickname: str = pydantic.Field(default="Twitter Bookmarks", min_length=1, max_length=120)
  collect_at: SetupCollectAt = pydantic.Field(default_factory=SetupCollectAt)


class FinishSetupCommand(pydantic.BaseModel):
  action: typing.Literal["finish"]


TwitterSetupCommand: typing.TypeAlias = typing.Annotated[
  GetStatusCommand
  | SaveOAuthAppCommand
  | BeginOAuthCommand
  | GetOAuthTransactionCommand
  | DisconnectAccountCommand
  | ConfigureBookmarkSourceCommand
  | FinishSetupCommand,
  pydantic.Field(discriminator="action"),
]
TwitterSetupResult: typing.TypeAlias = TwitterSetupStatus | OAuthTransactionView


class TwitterSetupError(RuntimeError): ...


class TwitterSetupConflict(TwitterSetupError): ...


class TwitterProviderError(TwitterSetupError): ...


def _extension():
  from . import Extension

  return Extension


def _state() -> TwitterExtensionState:
  return TwitterExtensionState.model_validate(_extension().get_state())


def _config() -> TwitterExtensionConfig:
  return _extension().get_config()


def _fingerprint(config: TwitterExtensionConfig) -> str:
  material = (
    f"inkcre-twitter-oauth-app\0{config.client_id}\0{config.client_secret}".encode()
  )
  return hashlib.sha256(material).hexdigest()


def _redirect_uri() -> str:
  try:
    base = PeerManager.get_current_config().http_public_base_url
  except (RuntimeError, ValueError) as error:
    raise TwitterSetupError("Core Peer public HTTP URL is unavailable") from error
  if base is None:
    raise TwitterSetupError("Core Peer public HTTP URL is not configured")
  return f"{base.rstrip('/')}/twitter/auth/callback"


def _pkce_pair() -> tuple[str, str]:
  verifier = secrets.token_urlsafe(48)
  digest = hashlib.sha256(verifier.encode()).digest()
  challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
  return verifier, challenge


def _bounded_provider_error(error: BaseException | str) -> str:
  value = str(error).replace("\r", " ").replace("\n", " ").strip()
  return (value or "Twitter authorization failed")[:240]


def _transaction_view(
  transaction_id: str,
  transaction: OAuthTransaction,
  *,
  authorize_url: str | None = None,
) -> OAuthTransactionView:
  return OAuthTransactionView(
    id=transaction_id,
    status=transaction.status,
    authorize_url=authorize_url,
    expires_at=transaction.expires_at,
    error=transaction.error,
  )


def _terminal(
  transaction: OAuthTransaction,
  status: typing.Literal["succeeded", "failed", "expired"],
  *,
  error: str | None = None,
) -> OAuthTransaction:
  return transaction.model_copy(
    update={
      "status": status,
      "provider_state": None,
      "pkce_verifier": None,
      "closed_at": _now(),
      "error": error,
    }
  )


def _invalidate_mismatched_oauth_state(
  config: TwitterExtensionConfig,
  state: TwitterExtensionState,
  *,
  reason: str,
) -> tuple[TwitterExtensionState, bool]:
  """Invalidate authorization material that belongs to another OAuth App."""
  fingerprint = _fingerprint(config)
  changed = state.account is not None and state.account.app_fingerprint != fingerprint
  if changed:
    state.account = None
  transactions = {
    key: _terminal(value, "expired", error=reason)
    if value.status in {"pending", "exchanging"} and value.app_fingerprint != fingerprint
    else value
    for key, value in state.oauth_transactions.items()
  }
  if transactions != state.oauth_transactions:
    state.oauth_transactions = transactions
    changed = True
  return state, changed


def _disable_bookmark_schedule(state: TwitterExtensionState) -> None:
  """Stop setup-owned collection while retaining its reusable Source and Cron."""
  if state.bookmark_cron_id is None:
    return
  with SessionLocal() as db:
    cron = db.get(CronModel, state.bookmark_cron_id)
  if cron is None or not cron.enabled:
    return
  CronManager.update(
    state.bookmark_cron_id,
    CronForm(
      schedule=cron.schedule,
      enabled=False,
      job_type=cron.job_type,
      job_parameters=dict(cron.job_parameters),
      job_timeout_seconds=cron.job_timeout_seconds,
    ),
  )


def _reconcile_oauth_state() -> TwitterExtensionState:
  """Reconcile direct deployment config writes before setup becomes reachable."""
  config = _config()
  state = _state()
  _, changed = _invalidate_mismatched_oauth_state(
    config,
    state.model_copy(deep=True),
    reason="OAuth App changed",
  )
  if not changed:
    return state
  _disable_bookmark_schedule(state)

  def reconcile(config_model, state_model):
    from . import TwitterExtensionConfig

    current_config = TwitterExtensionConfig.model_validate(config_model)
    current_state = TwitterExtensionState.model_validate(state_model)
    reconciled, _ = _invalidate_mismatched_oauth_state(
      current_config,
      current_state,
      reason="OAuth App changed",
    )
    return current_config, reconciled

  _, reconciled = _extension().mutate_config_and_state(reconcile)
  return TwitterExtensionState.model_validate(reconciled)


def _bookmark_source_status(
  state: TwitterExtensionState,
) -> tuple[
  int | None,
  int | None,
  tuple[BookmarkSourceView, ...],
  SetupCollectAt,
  bool,
]:
  with SessionLocal() as db:
    sources = db.exec(
      sqlmodel.select(SourceModel)
      .where(SourceModel.type == BOOKMARK_SOURCE_TYPE)
      .order_by(sqlmodel.col(SourceModel.id))
    ).all()
    views = tuple(
      BookmarkSourceView(
        source_id=source.id,
        nickname=source.nickname or "Twitter Bookmarks",
      )
      for source in sources
      if source.id is not None
    )
    source = next(
      (item for item in sources if item.id == state.bookmark_source_id),
      None,
    )
    cron = (
      None if state.bookmark_cron_id is None else db.get(CronModel, state.bookmark_cron_id)
    )

  collect_at = (
    SetupCollectAt.from_cron_schedule(cron.schedule) if cron is not None else None
  ) or SetupCollectAt()
  account = state.account
  expected_parameters = (
    None
    if source is None or account is None
    else {
      "source": source.id,
      "config": {
        "full": False,
        "result_limit": 40,
        "authorization_id": account.authorization_id,
      },
    }
  )
  ready = (
    cron is not None
    and cron.enabled
    and cron.job_type == SOURCE_COLLECT_JOB_TYPE
    and cron.job_parameters == expected_parameters
  )
  return (
    source.id if source is not None else None,
    cron.id if cron is not None else None,
    views,
    collect_at,
    ready,
  )


def get_setup_status() -> TwitterSetupStatus:
  config = _config()
  state = _reconcile_oauth_state()
  source_id, cron_id, sources, collect_at, source_ready = _bookmark_source_status(state)
  configured = bool(config.client_id and config.client_secret)
  account = state.account
  connected = (
    account is not None
    and configured
    and not account.reconnect_required
    and account.app_fingerprint == _fingerprint(config)
  )
  return TwitterSetupStatus(
    backend=config.backend,
    callback_url=_redirect_uri(),
    oauth_app_configured=configured,
    client_id=config.client_id or None,
    connected=connected,
    user_id=account.user_id if connected and account is not None else None,
    handle=account.handle if connected and account is not None else None,
    scopes=account.scopes if connected and account is not None else (),
    reconnect_required=bool(account and account.reconnect_required),
    bookmark_source_id=source_id,
    bookmark_cron_id=cron_id,
    bookmark_sources=sources,
    collect_at=collect_at,
    bookmark_source_ready=source_ready,
    ready=connected and source_ready,
  )


def save_oauth_app(body: SaveOAuthAppCommand) -> TwitterSetupStatus:
  current_config = _config()
  current_state = _state()
  next_config = current_config.model_copy(
    update={
      "backend": "official",
      "client_id": body.client_id.strip(),
      "client_secret": body.client_secret,
    }
  )
  fingerprint_changed = _fingerprint(next_config) != _fingerprint(current_config)
  has_live_setup = current_state.account is not None or any(
    value.status in {"pending", "exchanging"}
    for value in current_state.oauth_transactions.values()
  )
  if fingerprint_changed and has_live_setup and not body.confirm_account_reset:
    raise TwitterSetupConflict(
      "Replacing the OAuth App requires confirmation because it disconnects the account"
    )
  if fingerprint_changed:
    _disable_bookmark_schedule(current_state)

  def update(config_model, state_model):
    from . import TwitterExtensionConfig

    config = TwitterExtensionConfig.model_validate(config_model)
    state = TwitterExtensionState.model_validate(state_model)
    next_config = config.model_copy(
      update={
        "backend": "official",
        "client_id": body.client_id.strip(),
        "client_secret": body.client_secret,
      }
    )
    changed = _fingerprint(next_config) != _fingerprint(config)
    live_setup = state.account is not None or any(
      value.status in {"pending", "exchanging"}
      for value in state.oauth_transactions.values()
    )
    if changed and live_setup and not body.confirm_account_reset:
      raise TwitterSetupConflict(
        "Replacing the OAuth App requires confirmation because it disconnects the account"
      )
    if changed:
      state, _ = _invalidate_mismatched_oauth_state(
        next_config,
        state,
        reason="OAuth App changed",
      )
    return next_config, state

  _extension().mutate_config_and_state(update)
  return get_setup_status()


def begin_oauth() -> OAuthTransactionView:
  config = _config()
  if config.backend != "official" or not config.client_id or not config.client_secret:
    raise TwitterSetupConflict("Configure the Twitter OAuth App first")
  transaction_id = str(uuid.uuid4())
  provider_state = secrets.token_urlsafe(32)
  verifier, challenge = _pkce_pair()
  redirect_uri = _redirect_uri()
  now = _now()
  transaction = OAuthTransaction(
    status="pending",
    provider_state=provider_state,
    pkce_verifier=verifier,
    app_fingerprint=_fingerprint(config),
    redirect_uri=redirect_uri,
    created_at=now,
    expires_at=now + TRANSACTION_LIFETIME,
  )

  def update(model: pydantic.BaseModel) -> pydantic.BaseModel:
    state = TwitterExtensionState.model_validate(model)
    current_time = _now()
    transactions = {
      key: _terminal(value, "expired", error="Superseded by a newer setup")
      if value.status in {"pending", "exchanging"}
      else value
      for key, value in state.oauth_transactions.items()
      if value.closed_at is None or value.closed_at + TERMINAL_RETENTION > current_time
    }
    transactions[transaction_id] = transaction
    ordered = sorted(
      transactions.items(), key=lambda item: item[1].created_at, reverse=True
    )[:MAX_TRANSACTIONS]
    state.oauth_transactions = dict(ordered)
    return state

  _extension().mutate_state(update)
  client = OAuth2Client(
    client_id=config.client_id,
    client_secret=config.client_secret,
    scope=" ".join(SCOPES),
    redirect_uri=redirect_uri,
    token_endpoint_auth_method="client_secret_basic",
    timeout=10,
  )
  try:
    authorize_url, _ = client.create_authorization_url(
      AUTHORIZE_URL,
      state=provider_state,
      code_verifier=verifier,
      code_challenge=challenge,
      code_challenge_method="S256",
    )
  finally:
    typing.cast(httpx.Client, client).close()
  return _transaction_view(transaction_id, transaction, authorize_url=authorize_url)


def get_oauth_transaction(transaction_id: str) -> OAuthTransactionView:
  transaction = _state().oauth_transactions.get(transaction_id)
  if transaction is None:
    raise TwitterSetupError("OAuth transaction not found")
  if transaction.status in {"pending", "exchanging"} and transaction.expires_at <= _now():

    def expire(model: pydantic.BaseModel) -> pydantic.BaseModel:
      state = TwitterExtensionState.model_validate(model)
      current = state.oauth_transactions.get(transaction_id)
      if current is not None and current.status in {"pending", "exchanging"}:
        state.oauth_transactions[transaction_id] = _terminal(
          current, "expired", error="OAuth transaction expired"
        )
      return state

    state = TwitterExtensionState.model_validate(_extension().mutate_state(expire))
    transaction = state.oauth_transactions[transaction_id]
  return _transaction_view(transaction_id, transaction)


async def _exchange_code(
  config: TwitterExtensionConfig,
  transaction: OAuthTransaction,
  code: str,
) -> tuple[dict[str, typing.Any], str, str]:
  client = AsyncOAuth2Client(
    client_id=config.client_id,
    client_secret=config.client_secret,
    redirect_uri=transaction.redirect_uri,
    token_endpoint_auth_method="client_secret_basic",
    timeout=10,
  )
  try:
    try:
      token = await client.fetch_token(
        TOKEN_URL,
        code=code,
        code_verifier=transaction.pkce_verifier,
      )
    except OAuthError:
      raise TwitterProviderError("Twitter rejected the token exchange") from None
    except httpx.TimeoutException:
      raise TwitterProviderError("Twitter token exchange timed out") from None
    except httpx.HTTPStatusError as failure:
      raise TwitterProviderError(
        f"Twitter token exchange failed (HTTP {failure.response.status_code})"
      ) from None
    except httpx.HTTPError:
      raise TwitterProviderError("Twitter token exchange request failed") from None

    try:
      response = await typing.cast(httpx.AsyncClient, client).get(CURRENT_USER_URL)
      response.raise_for_status()
    except httpx.TimeoutException:
      raise TwitterProviderError("Twitter current-user lookup timed out") from None
    except httpx.HTTPStatusError as failure:
      status_code = failure.response.status_code
      if status_code == 402:
        message = (
          "Twitter current-user lookup requires X API credits or project access (HTTP 402)"
        )
      else:
        message = f"Twitter current-user lookup failed (HTTP {status_code})"
      raise TwitterProviderError(message) from None
    except httpx.HTTPError:
      raise TwitterProviderError("Twitter current-user lookup request failed") from None

    try:
      payload = response.json()
      if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
        raise TwitterProviderError(
          "Twitter current-user lookup returned an invalid response"
        )
      user = payload["data"]
      user_id = user.get("id")
      handle = user.get("username")
      if not isinstance(user_id, str) or not isinstance(handle, str):
        raise TwitterProviderError(
          "Twitter current-user lookup returned an incomplete response"
        )
      return dict(token), user_id, handle
    except (TypeError, ValueError):
      raise TwitterProviderError(
        "Twitter current-user lookup returned an invalid response"
      ) from None
  finally:
    await typing.cast(httpx.AsyncClient, client).aclose()


def _claim_callback(provider_state: str) -> tuple[str, OAuthTransaction]:
  box: dict[str, typing.Any] = {}

  def claim(model: pydantic.BaseModel) -> pydantic.BaseModel:
    state = TwitterExtensionState.model_validate(model)
    matched = next(
      (
        (key, value)
        for key, value in state.oauth_transactions.items()
        if value.provider_state == provider_state
      ),
      None,
    )
    if matched is None:
      raise TwitterSetupConflict("OAuth transaction is unknown")
    transaction_id, transaction = matched
    if transaction.status != "pending" or transaction.expires_at <= _now():
      raise TwitterSetupConflict("OAuth transaction is no longer active")
    box["id"] = transaction_id
    box["transaction"] = transaction
    state.oauth_transactions[transaction_id] = transaction.model_copy(
      update={"status": "exchanging"}
    )
    return state

  _extension().mutate_state(claim)
  return typing.cast(str, box["id"]), typing.cast(OAuthTransaction, box["transaction"])


def _finish_callback(
  transaction_id: str,
  transaction: OAuthTransaction,
  *,
  account: TwitterAccount | None = None,
  error: str | None = None,
) -> None:
  def finish(model: pydantic.BaseModel) -> pydantic.BaseModel:
    state = TwitterExtensionState.model_validate(model)
    current = state.oauth_transactions.get(transaction_id)
    if (
      current is None
      or current.status != "exchanging"
      or current.provider_state != transaction.provider_state
      or current.app_fingerprint != transaction.app_fingerprint
    ):
      raise TwitterSetupConflict("OAuth transaction was superseded")
    if account is None:
      state.oauth_transactions[transaction_id] = _terminal(
        current, "failed", error=error or "Twitter authorization failed"
      )
    else:
      state.account = account
      state.oauth_transactions[transaction_id] = _terminal(current, "succeeded")
    return state

  _extension().mutate_state(finish)


def _callback_html(status_code: int, title: str, message: str) -> HTMLResponse:
  safe_title = html.escape(title)
  safe_message = html.escape(message)
  return HTMLResponse(
    "<!doctype html><html><head><meta charset='utf-8'>"
    f"<title>{safe_title}</title></head><body><main><h1>{safe_title}</h1>"
    f"<p>{safe_message}</p><p>You can close this window.</p></main></body></html>",
    status_code=status_code,
  )


async def oauth_callback(
  code: str | None = None,
  state: str | None = None,
  error: str | None = None,
  error_description: str | None = None,
) -> HTMLResponse:
  del error_description
  transaction_id: str | None = None
  transaction: OAuthTransaction | None = None
  if not state:
    return _callback_html(400, "Twitter setup failed", "Missing OAuth state.")
  try:
    transaction_id, transaction = _claim_callback(state)
    if error:
      message = (
        "Twitter authorization was declined"
        if error == "access_denied"
        else "Twitter returned an authorization error"
      )
      _finish_callback(transaction_id, transaction, error=message)
      return _callback_html(400, "Twitter setup declined", message)
    if not code:
      raise TwitterSetupConflict("Missing authorization code")
    config = _config()
    if _fingerprint(config) != transaction.app_fingerprint:
      raise TwitterSetupConflict("OAuth App changed during authorization")
    token, user_id, handle = await _exchange_code(config, transaction, code)
    raw_scope = token.get("scope", "")
    scopes = tuple(raw_scope.split()) if isinstance(raw_scope, str) else SCOPES
    account = TwitterAccount(
      token=token,
      user_id=user_id,
      handle=handle,
      scopes=scopes,
      app_fingerprint=transaction.app_fingerprint,
      authorization_id=str(uuid.uuid4()),
      connected_at=_now(),
    )
    _finish_callback(transaction_id, transaction, account=account)
  except TwitterSetupConflict as failure:
    message = _bounded_provider_error(failure)
    try:
      if transaction_id is not None and transaction is not None:
        _finish_callback(transaction_id, transaction, error=message)
    except TwitterSetupError:
      pass
    return _callback_html(400, "Twitter setup failed", message)
  except (httpx.HTTPError, TwitterSetupError) as failure:
    message = _bounded_provider_error(failure)
    try:
      if transaction_id is not None and transaction is not None:
        _finish_callback(transaction_id, transaction, error=message)
    except TwitterSetupError:
      pass
    return _callback_html(502, "Twitter is unavailable", message)
  return _callback_html(200, "Twitter connected", "Authorization completed successfully.")


def disconnect_account() -> TwitterSetupStatus:
  _disable_bookmark_schedule(_state())

  def disconnect(model: pydantic.BaseModel) -> pydantic.BaseModel:
    state = TwitterExtensionState.model_validate(model)
    state.account = None
    state.oauth_transactions = {
      key: _terminal(value, "expired", error="Account disconnected")
      if value.status in {"pending", "exchanging"}
      else value
      for key, value in state.oauth_transactions.items()
    }
    return state

  _extension().mutate_state(disconnect)
  return get_setup_status()


def _bookmark_job_parameters(
  source_id: int, authorization_id: str
) -> dict[str, typing.Any]:
  return {
    "source": source_id,
    "config": {
      "full": False,
      "result_limit": 40,
      "authorization_id": authorization_id,
    },
  }


def configure_bookmark_source(body: ConfigureBookmarkSourceCommand) -> TwitterSetupStatus:
  state = _state()
  account = state.account
  if account is None or account.reconnect_required:
    raise TwitterSetupConflict("Connect a Twitter account first")
  if body.source_id is not None:
    with SessionLocal() as db:
      source = db.get(SourceModel, body.source_id)
    if source is None or source.type != BOOKMARK_SOURCE_TYPE:
      raise TwitterSetupConflict("Bookmark Source does not exist")
  else:
    source = SourceManager.create(
      BOOKMARK_SOURCE_TYPE,
      nickname=body.nickname,
    )
  source_id = source.id
  if source_id is None:
    raise TwitterSetupError("Bookmark Source has no identifier")
  try:
    form = CronForm(
      schedule=body.collect_at.cron_schedule(),
      enabled=False,
      job_type=SOURCE_COLLECT_JOB_TYPE,
      job_parameters=_bookmark_job_parameters(source_id, account.authorization_id),
    )
    cron = (
      CronManager.create(form)
      if state.bookmark_cron_id is None
      else CronManager.update(state.bookmark_cron_id, form)
    )
  except ValueError as error:
    raise TwitterSetupConflict(str(error)) from error
  if cron.id is None:
    raise TwitterSetupError("Bookmark schedule has no identifier")

  def select(model: pydantic.BaseModel) -> pydantic.BaseModel:
    selected = TwitterExtensionState.model_validate(model)
    if (
      selected.account is None
      or selected.account.authorization_id != account.authorization_id
    ):
      raise TwitterSetupConflict("Twitter account changed during setup")
    selected.bookmark_source_id = source_id
    selected.bookmark_cron_id = cron.id
    return selected

  _extension().mutate_state(select)
  return get_setup_status()


async def finish_setup() -> TwitterSetupStatus:
  from .api import OfficialAPI

  state = _state()
  account = state.account
  if account is None or account.reconnect_required:
    raise TwitterSetupConflict("Connect a Twitter account first")
  if state.bookmark_source_id is None or state.bookmark_cron_id is None:
    raise TwitterSetupConflict("Configure a Bookmark Source first")
  api = OfficialAPI.from_extension(expected_authorization_id=account.authorization_id)
  try:
    user_id, handle = await api.get_user()
  finally:
    await api.close()

  with SessionLocal() as db:
    source = db.get(SourceModel, state.bookmark_source_id)
    cron = db.get(CronModel, state.bookmark_cron_id)
  if source is None or source.type != BOOKMARK_SOURCE_TYPE or cron is None:
    raise TwitterSetupConflict("Bookmark collection resources no longer exist")
  source_id = source.id
  if source_id is None:
    raise TwitterSetupConflict("Bookmark Source has no identifier")
  schedule = cron.schedule
  rebound = CronManager.update(
    state.bookmark_cron_id,
    CronForm(
      schedule=schedule,
      enabled=True,
      job_type=SOURCE_COLLECT_JOB_TYPE,
      job_parameters=_bookmark_job_parameters(source_id, account.authorization_id),
      job_timeout_seconds=cron.job_timeout_seconds,
    ),
  )

  def update_identity(model: pydantic.BaseModel) -> pydantic.BaseModel:
    current = TwitterExtensionState.model_validate(model)
    if (
      current.account is None
      or current.account.authorization_id != account.authorization_id
      or current.bookmark_source_id != source_id
      or current.bookmark_cron_id != rebound.id
    ):
      raise TwitterSetupConflict("Twitter setup changed during Finish")
    current.account.user_id = user_id
    current.account.handle = handle
    return current

  _extension().mutate_state(update_identity)
  if rebound.id is None:
    raise TwitterSetupError("Bookmark schedule has no identifier")
  job = CronManager.run_now(rebound.id)
  if job.id is not None:
    await JobManager.check()
  return get_setup_status()


async def execute_setup_command(command: TwitterSetupCommand) -> TwitterSetupResult:
  if isinstance(command, GetStatusCommand):
    return get_setup_status()
  if isinstance(command, SaveOAuthAppCommand):
    return save_oauth_app(command)
  if isinstance(command, BeginOAuthCommand):
    return begin_oauth()
  if isinstance(command, GetOAuthTransactionCommand):
    return get_oauth_transaction(command.transaction_id)
  if isinstance(command, DisconnectAccountCommand):
    return disconnect_account()
  if isinstance(command, ConfigureBookmarkSourceCommand):
    return configure_bookmark_source(command)
  if isinstance(command, FinishSetupCommand):
    return await finish_setup()
  typing.assert_never(command)


def _http_error(error: TwitterSetupError) -> typing.NoReturn:
  if str(error) == "OAuth transaction not found":
    status = fastapi.status.HTTP_404_NOT_FOUND
  elif isinstance(error, TwitterProviderError):
    status = fastapi.status.HTTP_502_BAD_GATEWAY
  else:
    status = fastapi.status.HTTP_409_CONFLICT
  raise fastapi.HTTPException(status_code=status, detail=str(error)) from error


def register_setup_routes(router: fastapi.APIRouter) -> None:
  protected = fastapi.APIRouter(dependencies=[fastapi.Depends(require_peer_jwt)])

  @protected.post("/setup", response_model=TwitterSetupResult)
  async def setup_command(command: TwitterSetupCommand):
    try:
      return await execute_setup_command(command)
    except TwitterSetupError as failure:
      _http_error(failure)

  router.include_router(protected)
  router.add_api_route(
    "/auth/callback",
    oauth_callback,
    methods=["GET"],
    response_class=HTMLResponse,
  )
