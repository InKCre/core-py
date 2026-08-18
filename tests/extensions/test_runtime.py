"""Extension route-auth and reversible publication contracts."""

import time

import fastapi
from fastapi.testclient import TestClient
import jwt
import sqlmodel

from app.business.extension import ExtensionBase
from app.business.extension.runtime import ExtensionRuntimeRecord
from app.database_contract.constants import (
  JWT_ALGORITHM,
  JWT_AUDIENCE,
  JWT_ISSUER,
  JWT_ROLE,
)
from app.middleware import require_peer_jwt
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
  def _register_apis(cls, router: fastapi.APIRouter) -> None:
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
  def api_dependencies(cls) -> list:
    return []

  @classmethod
  def _register_apis(cls, router: fastapi.APIRouter) -> None:
    public = fastapi.APIRouter()
    protected = fastapi.APIRouter(dependencies=[fastapi.Depends(_require_extension_token)])
    public.get("/profile")(lambda: {"auth": "public"})
    protected.get("/memos")(lambda: {"auth": "extension"})
    router.include_router(public)
    router.include_router(protected)


def _record(extension_id: str) -> ExtensionRuntimeRecord:
  config: dict = {}
  state: dict = {}

  def persist_config(value):
    config.clear()
    config.update(value)

  def mutate_state(transform):
    next_state = transform(dict(state))
    state.clear()
    state.update(next_state)
    return dict(state)

  def mutate_config_and_state(transform):
    next_config, next_state = transform(dict(config), dict(state))
    config.clear()
    config.update(next_config)
    state.clear()
    state.update(next_state)
    return dict(config), dict(state)

  return ExtensionRuntimeRecord(
    extension_id=extension_id,
    config=dict(config),
    read_config=lambda: dict(config),
    persist_config=persist_config,
    read_state=lambda: dict(state),
    mutate_state=mutate_state,
    mutate_config_and_state=mutate_config_and_state,
    persist_config_schema=lambda _schema: None,
  )


def _start(extension: type[ExtensionBase], app: fastapi.FastAPI) -> None:
  extension.unpublish()
  extension.release_runtime()
  extension.on_start(app, _record(extension.__extid__))


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


def test_default_extension_routes_require_peer_jwt():
  app = fastapi.FastAPI()
  _start(_PeerExtension, app)
  try:
    client = TestClient(app)
    assert client.get("/test_peer/ping").status_code == 401
    assert client.get(
      "/test_peer/ping",
      headers={"Authorization": f"Bearer {_peer_token()}"},
    ).json() == {"auth": "peer"}
  finally:
    _PeerExtension.unpublish()
    _PeerExtension.release_runtime()


def test_self_authenticated_extension_composes_public_and_owned_dependencies():
  app = fastapi.FastAPI()
  _start(_SelfAuthenticatedExtension, app)
  try:
    client = TestClient(app)
    assert client.get("/test_self/profile").json() == {"auth": "public"}
    assert client.get("/test_self/memos").status_code == 401
    assert client.get(
      "/test_self/memos",
      headers={"X-Extension-Token": "accepted"},
    ).json() == {"auth": "extension"}
  finally:
    _SelfAuthenticatedExtension.unpublish()
    _SelfAuthenticatedExtension.release_runtime()


def test_unpublish_removes_routes_from_dispatch_and_openapi():
  app = fastapi.FastAPI()
  _start(_PeerExtension, app)
  client = TestClient(app)

  assert (
    client.get(
      "/test_peer/ping",
      headers={"Authorization": f"Bearer {_peer_token()}"},
    ).status_code
    == 200
  )
  assert "/test_peer/ping" in app.openapi()["paths"]

  _PeerExtension.unpublish()
  _PeerExtension.release_runtime()

  assert (
    client.get(
      "/test_peer/ping",
      headers={"Authorization": f"Bearer {_peer_token()}"},
    ).status_code
    == 404
  )
  assert "/test_peer/ping" not in app.openapi()["paths"]
