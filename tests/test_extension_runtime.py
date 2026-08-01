"""Extension route-auth, hot lifecycle, and config-update contracts."""

import asyncio
import time

import fastapi
from fastapi.testclient import TestClient
import jwt
import pydantic
import pytest
import sqlmodel

from app.business.extension import ExtensionBase, ExtensionManager
from app.business.extension.routing import ExtensionRouteMount
from app.database_contract.constants import (
  JWT_ALGORITHM,
  JWT_AUDIENCE,
  JWT_ISSUER,
  JWT_ROLE,
)
from app.middleware import require_peer_jwt
from app.schemas.extension import ExtensionModel
from app.settings import settings


def _peer_token() -> str:
  now = int(time.time())
  return jwt.encode(
    {
      "role": JWT_ROLE,
      "iss": JWT_ISSUER,
      "aud": JWT_AUDIENCE,
      "iat": now,
      "exp": now + 600,
    },
    settings.jwt_secret,
    algorithm=JWT_ALGORITHM,
  )


class _EmptyConfig(sqlmodel.SQLModel):
  pass


class _PeerExtension(
  ExtensionBase[_EmptyConfig],
  ext_id="test_peer",
  config_cls=_EmptyConfig,
):
  @classmethod
  def _register_apis(cls, router: fastapi.APIRouter):
    router.get("/ping")(lambda: {"auth": "peer"})


def _require_extension_token(request: fastapi.Request) -> None:
  if request.headers.get("X-Extension-Token") != "accepted":
    raise fastapi.HTTPException(status_code=401, detail="extension token required")


class _SelfAuthenticatedExtension(
  ExtensionBase[_EmptyConfig],
  ext_id="test_self",
  config_cls=_EmptyConfig,
):
  @classmethod
  def api_dependencies(cls):
    return []

  @classmethod
  def _register_apis(cls, router: fastapi.APIRouter):
    public = fastapi.APIRouter()
    protected = fastapi.APIRouter(dependencies=[fastapi.Depends(_require_extension_token)])
    public.get("/profile")(lambda: {"auth": "public"})
    protected.get("/memos")(lambda: {"auth": "extension"})
    router.include_router(public)
    router.include_router(protected)


def _extension_model(extid: str, config: dict | None = None) -> ExtensionModel:
  return ExtensionModel(
    id=extid,
    version="0.1.0",
    enabled=[],
    config=config or {},
  )


def test_core_peer_dependency_protects_only_its_route_tree():
  app = fastapi.FastAPI()
  protected = fastapi.APIRouter(dependencies=[fastapi.Depends(require_peer_jwt)])
  protected.get("/core")(lambda: {"ok": True})
  app.include_router(protected)
  app.get("/public")(lambda: {"ok": True})
  client = TestClient(app)

  assert client.get("/public").status_code == 200
  unauthorized = client.get("/core")
  assert unauthorized.status_code == 401
  assert unauthorized.headers["www-authenticate"] == "Bearer"
  assert (
    client.get("/core", headers={"Authorization": f"Bearer {_peer_token()}"}).status_code
    == 200
  )
  assert client.get("/unknown").status_code == 404


def test_application_exposes_health_but_protects_core_routes():
  from run import api_app

  client = TestClient(api_app)

  assert client.get("/livez").status_code == 200
  unauthorized = client.get("/extensions")
  assert unauthorized.status_code == 401
  assert unauthorized.headers["www-authenticate"] == "Bearer"
  assert client.get("/unknown").status_code == 404


def test_default_extension_routes_require_peer_jwt():
  app = fastapi.FastAPI()
  mount = ExtensionRouteMount(
    app,
    _PeerExtension.on_start(_extension_model("test_peer")),
  )
  mount.publish()
  client = TestClient(app)

  assert client.get("/test_peer/ping").status_code == 401
  assert client.get(
    "/test_peer/ping", headers={"Authorization": f"Bearer {_peer_token()}"}
  ).json() == {"auth": "peer"}


def test_self_authenticated_extension_composes_public_and_owned_dependencies():
  app = fastapi.FastAPI()
  mount = ExtensionRouteMount(
    app,
    _SelfAuthenticatedExtension.on_start(_extension_model("test_self")),
  )
  mount.publish()
  client = TestClient(app)

  assert client.get("/test_self/profile").json() == {"auth": "public"}
  assert client.get("/test_self/memos").status_code == 401
  assert client.get(
    "/test_self/memos", headers={"X-Extension-Token": "accepted"}
  ).json() == {"auth": "extension"}


def test_retained_extension_router_is_removed_from_dispatch_and_openapi():
  app = fastapi.FastAPI()
  router = fastapi.APIRouter(prefix="/hot")
  router.get("/ping")(lambda: {"ok": True})
  mount = ExtensionRouteMount(app, router)
  mount.publish()
  client = TestClient(app)

  assert client.get("/hot/ping").status_code == 200
  assert "/hot/ping" in app.openapi()["paths"]

  mount.unpublish()

  assert client.get("/hot/ping").status_code == 404
  assert "/hot/ping" not in app.openapi()["paths"]

  replacement = fastapi.APIRouter(prefix="/hot")
  replacement.get("/ping")(lambda: {"generation": 2})
  replacement_mount = ExtensionRouteMount(app, replacement)
  replacement_mount.publish()
  assert client.get("/hot/ping").json() == {"generation": 2}


def test_close_unpublishes_before_cleanup_and_can_be_retried():
  class _FailOnce:
    attempts = 0

    @classmethod
    async def on_close(cls):
      cls.attempts += 1
      if cls.attempts == 1:
        raise RuntimeError("close failed")

  app = fastapi.FastAPI()
  router = fastapi.APIRouter(prefix="/closing")
  router.get("/ping")(lambda: {"ok": True})
  mount = ExtensionRouteMount(app, router)
  mount.publish()
  client = TestClient(app)
  ExtensionManager.RUNNING_EXTENSIONS["closing"] = _FailOnce  # type: ignore[assignment]
  ExtensionManager.ROUTE_MOUNTS["closing"] = mount

  try:
    with pytest.raises(RuntimeError, match="close failed"):
      asyncio.run(ExtensionManager.close("closing"))
    assert client.get("/closing/ping").status_code == 404
    assert "closing" in ExtensionManager.RUNNING_EXTENSIONS

    asyncio.run(ExtensionManager.close("closing"))
    assert "closing" not in ExtensionManager.RUNNING_EXTENSIONS
    assert "closing" not in ExtensionManager.ROUTE_MOUNTS
  finally:
    ExtensionManager.RUNNING_EXTENSIONS.pop("closing", None)
    ExtensionManager.ROUTE_MOUNTS.pop("closing", None)


def test_installed_decoders_load_without_starting_extension(monkeypatch):
  loaded: list[str] = []

  class _DecoderOnly:
    @classmethod
    def load_decoders(cls):
      loaded.append("decoder")

  monkeypatch.setattr(
    ExtensionManager,
    "get_installed",
    classmethod(lambda cls: (_extension_model("decoder_only"),)),
  )
  monkeypatch.setattr(
    ExtensionManager,
    "_load_extension_class",
    classmethod(lambda cls, extid: _DecoderOnly),
  )

  ExtensionManager.load_installed_decoders()

  assert loaded == ["decoder"]
  assert "decoder_only" not in ExtensionManager.RUNNING_EXTENSIONS


class _StrictConfig(sqlmodel.SQLModel):
  model_config = pydantic.ConfigDict(extra="forbid")

  token: str | None = None
  page_size: int = 50


class _ConfiguredExtension(
  ExtensionBase[_StrictConfig],
  ext_id="configured",
  config_cls=_StrictConfig,
):
  @classmethod
  def _register_apis(cls, router: fastapi.APIRouter):
    pass


class _Result:
  def __init__(self, extension: ExtensionModel | None):
    self.extension = extension

  def first(self):
    return self.extension


class _Session:
  def __init__(self, extension: ExtensionModel | None):
    self.extension = extension
    self.commits = 0

  def __enter__(self):
    return self

  def __exit__(self, _error_type, _error_value, _traceback):
    return None

  def exec(self, _query):
    return _Result(self.extension)

  def add(self, _extension):
    return None

  def commit(self):
    self.commits += 1

  def refresh(self, _extension):
    return None


def test_config_patch_is_validated_before_persist_and_applied_after_commit(monkeypatch):
  model = _extension_model(
    "configured",
    {"token": "old", "page_size": 25},
  )
  session = _Session(model)
  monkeypatch.setattr(
    "app.business.extension.main.SessionLocal",
    lambda: session,
  )
  monkeypatch.setattr(
    ExtensionManager,
    "_load_extension_class",
    classmethod(lambda cls, extid: _ConfiguredExtension),
  )
  ExtensionManager.RUNNING_EXTENSIONS["configured"] = _ConfiguredExtension
  _ConfiguredExtension.config = _StrictConfig(token="runtime-old", page_size=10)

  try:
    updated = ExtensionManager.update_config("configured", {"token": None})
    assert updated is model
    assert model.config == {"token": None, "page_size": 25}
    assert session.commits == 1
    assert _ConfiguredExtension.config == _StrictConfig(token=None, page_size=25)
  finally:
    ExtensionManager.RUNNING_EXTENSIONS.pop("configured", None)


def test_invalid_config_patch_changes_neither_database_nor_runtime(monkeypatch):
  original = {"token": "old", "page_size": 25}
  model = _extension_model("configured", original.copy())
  session = _Session(model)
  monkeypatch.setattr(
    "app.business.extension.main.SessionLocal",
    lambda: session,
  )
  monkeypatch.setattr(
    ExtensionManager,
    "_load_extension_class",
    classmethod(lambda cls, extid: _ConfiguredExtension),
  )
  ExtensionManager.RUNNING_EXTENSIONS["configured"] = _ConfiguredExtension
  runtime_config = _StrictConfig(token="runtime-old", page_size=10)
  _ConfiguredExtension.config = runtime_config

  try:
    with pytest.raises(pydantic.ValidationError):
      ExtensionManager.update_config("configured", {"page_size": "invalid"})
    assert model.config == original
    assert session.commits == 0
    assert _ConfiguredExtension.config is runtime_config
  finally:
    ExtensionManager.RUNNING_EXTENSIONS.pop("configured", None)


def test_omitted_config_patch_preserves_persisted_and_runtime_values(monkeypatch):
  model = _extension_model(
    "configured",
    {"token": "kept", "page_size": 25},
  )
  session = _Session(model)
  monkeypatch.setattr("app.business.extension.main.SessionLocal", lambda: session)
  monkeypatch.setattr(
    ExtensionManager,
    "_load_extension_class",
    classmethod(lambda cls, extid: _ConfiguredExtension),
  )
  ExtensionManager.RUNNING_EXTENSIONS["configured"] = _ConfiguredExtension
  _ConfiguredExtension.config = _StrictConfig(token="kept", page_size=25)

  try:
    ExtensionManager.update_config("configured", {})

    assert model.config == {"token": "kept", "page_size": 25}
    assert _ConfiguredExtension.config == _StrictConfig(
      token="kept",
      page_size=25,
    )
  finally:
    ExtensionManager.RUNNING_EXTENSIONS.pop("configured", None)


def test_config_commit_failure_changes_neither_database_nor_runtime(monkeypatch):
  original = {"token": "old", "page_size": 25}
  model = _extension_model("configured", original.copy())

  class _CommitFailureSession(_Session):
    def __exit__(self, _error_type, _error_value, _traceback):
      if _error_type is not None and self.extension is not None:
        self.extension.config = original.copy()
      return None

    def commit(self):
      self.commits += 1
      raise RuntimeError("injected commit failure")

  session = _CommitFailureSession(model)
  monkeypatch.setattr("app.business.extension.main.SessionLocal", lambda: session)
  monkeypatch.setattr(
    ExtensionManager,
    "_load_extension_class",
    classmethod(lambda cls, extid: _ConfiguredExtension),
  )
  ExtensionManager.RUNNING_EXTENSIONS["configured"] = _ConfiguredExtension
  runtime_config = _StrictConfig(token="runtime-old", page_size=10)
  _ConfiguredExtension.config = runtime_config

  try:
    with pytest.raises(RuntimeError, match="commit failure"):
      ExtensionManager.update_config("configured", {"token": "new"})

    assert model.config == original
    assert _ConfiguredExtension.config is runtime_config
  finally:
    ExtensionManager.RUNNING_EXTENSIONS.pop("configured", None)
