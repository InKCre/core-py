"""Whole-Extension setup workflow for the Twitter Extension."""

from __future__ import annotations

import base64
import datetime
import hashlib
import html
import secrets
import typing
import uuid

from authlib.integrations.httpx_client import (  # pyrefly: ignore[untyped-import]
  AsyncOAuth2Client,
  OAuth2Client,
)
from authlib.integrations.base_client.errors import OAuthError  # pyrefly: ignore[untyped-import]
import fastapi
from fastapi.responses import HTMLResponse
import httpx
import sqlmodel

from app.business.source import SourceManager
from app.engine import SessionLocal
from app.schemas.source import (
  CollectAt,
  SourceCollectJobModel,
  SourceCollectJobStatus,
  SourceModel,
)


if typing.TYPE_CHECKING:
  from . import TwitterExtensionConfig


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


class TwitterAccount(sqlmodel.SQLModel):
  token: dict[str, typing.Any]
  user_id: str
  handle: str
  scopes: tuple[str, ...] = ()
  app_fingerprint: str
  authorization_id: str
  connected_at: datetime.datetime
  reconnect_required: bool = False


class OAuthTransaction(sqlmodel.SQLModel):
  status: typing.Literal["pending", "exchanging", "succeeded", "failed", "expired"]
  provider_state: str | None = None
  pkce_verifier: str | None = None
  app_fingerprint: str
  redirect_uri: str
  created_at: datetime.datetime
  expires_at: datetime.datetime
  closed_at: datetime.datetime | None = None
  error: str | None = None


class TwitterExtensionState(sqlmodel.SQLModel):
  account: TwitterAccount | None = None
  oauth_transactions: dict[str, OAuthTransaction] = sqlmodel.Field(default_factory=dict)
  bookmark_source_id: int | None = None


class OAuthAppInput(sqlmodel.SQLModel):
  client_id: str = sqlmodel.Field(min_length=1, max_length=256)
  client_secret: str = sqlmodel.Field(min_length=1, max_length=1024)
  confirm_account_reset: bool = False


class BookmarkSourceInput(sqlmodel.SQLModel):
  source_id: int | None = None
  nickname: str = sqlmodel.Field(default="Twitter Bookmarks", min_length=1, max_length=120)
  collect_at: CollectAt = sqlmodel.Field(default_factory=CollectAt)


class OAuthTransactionView(sqlmodel.SQLModel):
  id: str
  status: str
  authorize_url: str | None = None
  expires_at: datetime.datetime
  error: str | None = None


class TwitterSetupStatus(sqlmodel.SQLModel):
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
  bookmark_sources: tuple[BookmarkSourceInput, ...] = ()
  bookmark_source_ready: bool = False
  ready: bool = False


class TwitterSetupError(RuntimeError): ...


class TwitterSetupConflict(TwitterSetupError): ...


class TwitterProviderError(TwitterSetupError): ...


def _extension():
  from . import Extension

  return Extension


def _state() -> TwitterExtensionState:
  return TwitterExtensionState.model_validate(_extension().get_state().model_dump())


def _config() -> TwitterExtensionConfig:
  return _extension().get_config()


def _fingerprint(config: TwitterExtensionConfig) -> str:
  material = (
    f"inkcre-twitter-oauth-app\0{config.client_id}\0{config.client_secret}".encode()
  )
  return hashlib.sha256(material).hexdigest()


def _redirect_uri() -> str:
  from app.settings import settings

  base = (settings.client_base_url or "").rstrip("/")
  if not base:
    raise TwitterSetupError("Core API base URL is not configured")
  return f"{base}/twitter/auth/callback"


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


def _source_and_job_status(
  state: TwitterExtensionState,
) -> tuple[int | None, tuple[BookmarkSourceInput, ...], bool]:
  source_id = state.bookmark_source_id
  account = state.account
  with SessionLocal() as db:
    sources = db.exec(
      sqlmodel.select(SourceModel)
      .where(SourceModel.type == BOOKMARK_SOURCE_TYPE)
      .order_by(sqlmodel.col(SourceModel.id))
    ).all()
    source_views = tuple(
      BookmarkSourceInput(
        source_id=source.id,
        nickname=source.nickname or "Twitter Bookmarks",
        collect_at=source.collect_at or CollectAt(),
      )
      for source in sources
    )
    if source_id is None or account is None:
      return source_id, source_views, False
    source = next((item for item in sources if item.id == source_id), None)
    if source is None:
      return None, source_views, False
    jobs = db.exec(
      sqlmodel.select(SourceCollectJobModel)
      .where(SourceCollectJobModel.source == source_id)
      .order_by(sqlmodel.col(SourceCollectJobModel.id).desc())
    ).all()
  ready = any(
    job.status != SourceCollectJobStatus.FAILED
    and (job.config or {}).get("authorization_id") == account.authorization_id
    for job in jobs
  )
  return source_id, source_views, ready


def get_setup_status() -> TwitterSetupStatus:
  config = _config()
  state = _state()
  source_id, sources, source_ready = _source_and_job_status(state)
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
    bookmark_sources=sources,
    bookmark_source_ready=source_ready,
    ready=connected and source_ready,
  )


def save_oauth_app(body: OAuthAppInput) -> TwitterSetupStatus:
  extension = _extension()

  def update(config_model, state_model):
    from . import TwitterExtensionConfig

    config = TwitterExtensionConfig.model_validate(config_model.model_dump())
    state = TwitterExtensionState.model_validate(state_model.model_dump())
    old_fingerprint = _fingerprint(config)
    next_config = config.model_copy(
      update={
        "backend": "official",
        "client_id": body.client_id.strip(),
        "client_secret": body.client_secret,
      }
    )
    fingerprint_changed = _fingerprint(next_config) != old_fingerprint
    has_live_setup = state.account is not None or any(
      value.status in {"pending", "exchanging"}
      for value in state.oauth_transactions.values()
    )
    if fingerprint_changed and has_live_setup and not body.confirm_account_reset:
      raise TwitterSetupConflict(
        "Replacing the OAuth App requires confirmation because it disconnects the account"
      )
    config.backend = "official"
    config.client_id = body.client_id.strip()
    config.client_secret = body.client_secret
    if fingerprint_changed:
      state.account = None
      state.oauth_transactions = {
        key: _terminal(value, "expired", error="OAuth App changed")
        if value.status in {"pending", "exchanging"}
        else value
        for key, value in state.oauth_transactions.items()
      }
    return config, state

  extension.mutate_config_and_state(update)
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

  def update(model: sqlmodel.SQLModel) -> sqlmodel.SQLModel:
    state = TwitterExtensionState.model_validate(model.model_dump())
    now = _now()
    transactions = {
      key: _terminal(value, "expired", error="Superseded by a newer setup")
      if value.status in {"pending", "exchanging"}
      else value
      for key, value in state.oauth_transactions.items()
      if value.closed_at is None or value.closed_at + TERMINAL_RETENTION > now
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

    def expire(model: sqlmodel.SQLModel) -> sqlmodel.SQLModel:
      state = TwitterExtensionState.model_validate(model.model_dump())
      current = state.oauth_transactions.get(transaction_id)
      if current is not None and current.status in {"pending", "exchanging"}:
        state.oauth_transactions[transaction_id] = _terminal(
          current, "expired", error="OAuth transaction expired"
        )
      return state

    state = typing.cast(TwitterExtensionState, _extension().mutate_state(expire))
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
      response = await typing.cast(httpx.AsyncClient, client).get(CURRENT_USER_URL)
      response.raise_for_status()
      payload = response.json()
      if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
        raise TwitterProviderError("Twitter returned an invalid account response")
      user = payload["data"]
      user_id = user.get("id")
      handle = user.get("username")
      if not isinstance(user_id, str) or not isinstance(handle, str):
        raise TwitterProviderError("Twitter user response is incomplete")
      return dict(token), user_id, handle
    except OAuthError:
      raise TwitterProviderError("Twitter rejected the authorization exchange") from None
    except httpx.TimeoutException:
      raise TwitterProviderError("Twitter authorization timed out") from None
    except httpx.HTTPError:
      raise TwitterProviderError("Twitter authorization request failed") from None
    except (TypeError, ValueError):
      raise TwitterProviderError(
        "Twitter returned an invalid authorization response"
      ) from None
  finally:
    await typing.cast(httpx.AsyncClient, client).aclose()


def _claim_callback(provider_state: str) -> tuple[str, OAuthTransaction]:
  box: dict[str, typing.Any] = {}

  def claim(model: sqlmodel.SQLModel) -> sqlmodel.SQLModel:
    state = TwitterExtensionState.model_validate(model.model_dump())
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
  def finish(model: sqlmodel.SQLModel) -> sqlmodel.SQLModel:
    state = TwitterExtensionState.model_validate(model.model_dump())
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
  def disconnect(model: sqlmodel.SQLModel) -> sqlmodel.SQLModel:
    state = TwitterExtensionState.model_validate(model.model_dump())
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


def ensure_bookmark_source(body: BookmarkSourceInput) -> TwitterSetupStatus:
  state = _state()
  if state.account is None or state.account.reconnect_required:
    raise TwitterSetupConflict("Connect a Twitter account first")
  if body.source_id is not None:
    with SessionLocal() as db:
      source = db.get(SourceModel, body.source_id)
    if source is None or source.type != BOOKMARK_SOURCE_TYPE:
      raise TwitterSetupConflict("Bookmark Source does not exist")
  else:
    source, _ = SourceManager.ensure_exists(
      BOOKMARK_SOURCE_TYPE,
      nickname=body.nickname,
      collect_at=body.collect_at,
    )
  if source.id is None:
    raise TwitterSetupError("Bookmark Source has no identifier")

  def select(model: sqlmodel.SQLModel) -> sqlmodel.SQLModel:
    selected = TwitterExtensionState.model_validate(model.model_dump())
    selected.bookmark_source_id = source.id
    return selected

  _extension().mutate_state(select)
  return get_setup_status()


async def finish_setup() -> TwitterSetupStatus:
  from .api import OfficialAPI
  from app.business.source import SourceCollectJobManager

  state = _state()
  account = state.account
  if account is None or account.reconnect_required:
    raise TwitterSetupConflict("Connect a Twitter account first")
  if state.bookmark_source_id is None:
    raise TwitterSetupConflict("Configure a Bookmark Source first")
  api = OfficialAPI.from_extension(expected_authorization_id=account.authorization_id)
  try:
    user_id, handle = await api.get_user()
  finally:
    await api.close()

  def update_identity(model: sqlmodel.SQLModel) -> sqlmodel.SQLModel:
    current = TwitterExtensionState.model_validate(model.model_dump())
    if (
      current.account is None
      or current.account.authorization_id != account.authorization_id
    ):
      raise TwitterSetupConflict("Twitter account changed during setup")
    current.account.user_id = user_id
    current.account.handle = handle
    return current

  _extension().mutate_state(update_identity)
  with SessionLocal() as db:
    source = db.get(SourceModel, state.bookmark_source_id)
    if source is None or source.type != BOOKMARK_SOURCE_TYPE:
      raise TwitterSetupConflict("Bookmark Source no longer exists")
  SourceCollectJobManager.ensure(
    state.bookmark_source_id,
    {
      "full": False,
      "result_limit": 40,
      "authorization_id": account.authorization_id,
    },
  )
  await SourceCollectJobManager.check()
  return get_setup_status()


def _http_error(error: TwitterSetupError) -> typing.NoReturn:
  status = 404 if str(error) == "OAuth transaction not found" else 409
  raise fastapi.HTTPException(status_code=status, detail=str(error)) from error


def register_setup_routes(router: fastapi.APIRouter) -> None:
  @router.get("/setup", response_model=TwitterSetupStatus)
  def status():
    return get_setup_status()

  @router.put("/setup/oauth-app", response_model=TwitterSetupStatus)
  def oauth_app(body: OAuthAppInput):
    try:
      return save_oauth_app(body)
    except TwitterSetupError as failure:
      _http_error(failure)

  @router.post(
    "/setup/oauth-transactions",
    response_model=OAuthTransactionView,
    status_code=fastapi.status.HTTP_201_CREATED,
  )
  def start_oauth():
    try:
      return begin_oauth()
    except TwitterSetupError as failure:
      _http_error(failure)

  @router.get(
    "/setup/oauth-transactions/{transaction_id}",
    response_model=OAuthTransactionView,
  )
  def transaction(transaction_id: str):
    try:
      return get_oauth_transaction(transaction_id)
    except TwitterSetupError as failure:
      _http_error(failure)

  @router.delete("/setup/account", response_model=TwitterSetupStatus)
  def disconnect():
    return disconnect_account()

  @router.post("/setup/bookmark-source", response_model=TwitterSetupStatus)
  def bookmark_source(body: BookmarkSourceInput):
    try:
      return ensure_bookmark_source(body)
    except TwitterSetupError as failure:
      _http_error(failure)

  @router.post("/setup/finish", response_model=TwitterSetupStatus)
  async def finish():
    try:
      return await finish_setup()
    except TwitterSetupError as failure:
      _http_error(failure)

  router.add_api_route(
    "/auth/callback",
    oauth_callback,
    methods=["GET"],
    response_class=HTMLResponse,
  )
