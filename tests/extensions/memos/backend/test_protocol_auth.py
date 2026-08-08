"""Memos public/PAT auth and hot route availability matrix."""

import time

import fastapi
from fastapi.testclient import TestClient
import jwt
import pytest

from app.business.extension.routing import ExtensionRouteMount
from app.database_contract.constants import (
  JWT_ALGORITHM,
  JWT_AUDIENCE,
  JWT_ISSUER,
  JWT_ROLE,
)
from app.schemas.extension import ExtensionModel
from app.settings import settings
from extensions.memos import Extension
from extensions.memos.config import MemosConfig
from extensions.memos.family import (
  CanonicalMemo,
  MemoApplicationService,
  MemoCursor,
  MemoNotFoundError,
  MemoPage,
  SolvedMemo,
)


PAT = "memos_pat_" + "A" * 32
NEW_PAT = "memos_pat_" + "B" * 32


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


def _publish(config: dict | None = None):
  app = fastapi.FastAPI()
  model = ExtensionModel(
    id="memos",
    version="0.1.0",
    enabled=[],
    config=config or {},
  )
  mount = ExtensionRouteMount(app, Extension.on_start(model))
  mount.publish()
  return app, mount, TestClient(app)


@pytest.mark.parametrize(
  "authorization",
  [None, "not-bearer", "Bearer wrong", f"Bearer {_peer_token()}"],
)
def test_public_probe_ignores_authorization(authorization):
  _, _, client = _publish()
  headers = {} if authorization is None else {"Authorization": authorization}

  response = client.get("/memos/api/v1/instance/profile", headers=headers)

  assert response.status_code == 200
  assert response.json() == {"version": "0.29.1"}


def test_v0_status_remains_unregistered():
  _, _, client = _publish({"personal_access_token": PAT})

  assert client.get("/memos/api/v1/status").status_code == 404


@pytest.mark.parametrize(
  ("method", "path", "expected"),
  [
    ("GET", "/memos/api/v1/memos/17", 405),
    ("GET", "/memos/api/v1/memos/17/reactions", 404),
    ("PATCH", "/memos/api/v1/memos/17/relations", 404),
    ("GET", "/memos/api/v1/users", 404),
    ("GET", "/memos/admin/pats", 404),
  ],
)
def test_outside_bounded_memos_surface_never_returns_false_success(
  method,
  path,
  expected,
):
  _, _, client = _publish({"personal_access_token": PAT})

  response = client.request(
    method,
    path,
    headers={"Authorization": f"Bearer {PAT}"},
  )

  assert response.status_code == expected


@pytest.mark.parametrize("raw_id", ["0", "-1", "017", "+17", "memo"])
def test_noncanonical_memo_block_identity_is_400(raw_id):
  _, _, client = _publish({"personal_access_token": PAT})

  response = client.delete(
    f"/memos/api/v1/memos/{raw_id}",
    headers={"Authorization": f"Bearer {PAT}"},
  )

  assert response.status_code == 400


@pytest.mark.parametrize(
  ("method", "path", "params", "content"),
  [
    ("GET", "/memos/api/v1/memos", {}, None),
    (
      "GET",
      "/memos/api/v1/memos",
      {"filter": 'creator == "users/inkcre"', "pageToken": "broken!"},
      None,
    ),
    (
      "PATCH",
      "/memos/api/v1/memos/17",
      {"updateMask": "unknown"},
      b'{"content":"x"}',
    ),
    ("POST", "/memos/api/v1/memos", {}, b"not-json"),
    ("POST", "/memos/api/v1/memos/17/comments", {}, b"not-json"),
  ],
)
def test_protocol_validation_failures_are_400(method, path, params, content):
  _, _, client = _publish({"personal_access_token": PAT})

  response = client.request(
    method,
    path,
    params=params,
    content=content,
    headers={
      "Authorization": f"Bearer {PAT}",
      "Content-Type": "application/json",
    },
  )

  assert response.status_code == 400


@pytest.mark.parametrize(
  "authorization",
  [None, "not-bearer", "Bearer wrong", f"Bearer {_peer_token()}"],
)
def test_protected_routes_reject_missing_malformed_and_foreign_tokens(authorization):
  _, _, client = _publish({"personal_access_token": PAT})
  headers = {} if authorization is None else {"Authorization": authorization}

  response = client.get("/memos/api/v1/auth/me", headers=headers)

  assert response.status_code == 401
  assert response.headers["www-authenticate"] == "Bearer"


def test_pat_returns_stable_current_user_and_general_settings():
  _, _, client = _publish({"personal_access_token": PAT})
  headers = {"Authorization": f"Bearer {PAT}"}

  current_user = client.get("/memos/api/v1/auth/me", headers=headers)
  settings_response = client.get(
    "/memos/api/v1/users/inkcre/settings/GENERAL",
    headers=headers,
  )

  assert current_user.status_code == 200
  assert current_user.json()["user"]["name"] == "users/inkcre"
  assert settings_response.json() == {"generalSetting": {"memoVisibility": "PRIVATE"}}
  assert (
    client.get(
      "/memos/api/v1/users/other/settings/GENERAL",
      headers=headers,
    ).status_code
    == 404
  )


def test_text_memo_create_returns_resolver_shaped_native_response(monkeypatch):
  _, _, client = _publish({"personal_access_token": PAT})

  async def create(_cls, canonical, *, attachment_ids=()):
    assert attachment_ids == ()
    return SolvedMemo(block_id=17, canonical=canonical)

  monkeypatch.setattr(MemoApplicationService, "create", classmethod(create))
  response = client.post(
    "/memos/api/v1/memos",
    headers={"Authorization": f"Bearer {PAT}"},
    json={
      "content": "A small thought #inkcre",
      "visibility": "PRIVATE",
      "attachments": [],
      "createTime": "2026-08-01T08:00:00Z",
    },
  )

  assert response.status_code == 200
  assert response.json() == {
    "name": "memos/17",
    "state": "NORMAL",
    "creator": "users/inkcre",
    "createTime": "2026-08-01T08:00:00Z",
    "updateTime": "2026-08-01T08:00:00Z",
    "content": "A small thought #inkcre",
    "visibility": "PRIVATE",
    "pinned": False,
    "attachments": [],
  }


def test_list_returns_native_page_and_terminal_empty_token(monkeypatch):
  _, _, client = _publish({"personal_access_token": PAT})
  canonical = CanonicalMemo(
    body="listed",
    created_at=None,
    updated_at=None,
  )

  async def list_top_level(_cls, **kwargs):
    assert kwargs == {"archived": False, "limit": 200, "after": None}
    return MemoPage(
      memos=(SolvedMemo(block_id=17, canonical=canonical),),
      next_cursor=None,
    )

  monkeypatch.setattr(
    MemoApplicationService,
    "list_top_level",
    classmethod(list_top_level),
  )
  response = client.get(
    "/memos/api/v1/memos",
    headers={"Authorization": f"Bearer {PAT}"},
    params={
      "pageSize": "200",
      "pageToken": "",
      "state": "NORMAL",
      "filter": 'creator == "users/inkcre"',
    },
  )

  assert response.status_code == 200
  assert response.json()["nextPageToken"] == ""
  assert [memo["name"] for memo in response.json()["memos"]] == ["memos/17"]


def test_list_returns_query_bound_next_page_token(monkeypatch):
  _, _, client = _publish({"personal_access_token": PAT})
  cursor = MemoCursor(created_at=None, block_id=17)

  async def list_top_level(_cls, **_kwargs):
    return MemoPage(memos=(), next_cursor=cursor)

  monkeypatch.setattr(
    MemoApplicationService,
    "list_top_level",
    classmethod(list_top_level),
  )
  response = client.get(
    "/memos/api/v1/memos",
    headers={"Authorization": f"Bearer {PAT}"},
    params={
      "state": "ARCHIVED",
      "filter": 'creator == "users/inkcre"',
    },
  )

  assert response.status_code == 200
  assert response.json()["nextPageToken"]


def test_missing_update_mask_infers_exact_present_root_fields(monkeypatch):
  _, _, client = _publish({"personal_access_token": PAT})
  original = CanonicalMemo(
    body="before",
    created_at=None,
    updated_at=None,
    pinned=True,
  )

  async def update(_cls, block_id, patch, *, attachment_ids=None):
    assert block_id == 17
    assert attachment_ids is None
    assert patch.model_fields_set == {"body", "pinned"}
    return SolvedMemo(block_id=block_id, canonical=patch.apply(original))

  monkeypatch.setattr(MemoApplicationService, "update", classmethod(update))
  response = client.patch(
    "/memos/api/v1/memos/17",
    headers={"Authorization": f"Bearer {PAT}"},
    json={"content": "", "pinned": False},
  )

  assert response.status_code == 200
  assert response.json()["content"] == ""
  assert response.json()["pinned"] is False


def test_explicit_update_mask_does_not_infer_other_body_fields(monkeypatch):
  _, _, client = _publish({"personal_access_token": PAT})
  original = CanonicalMemo(
    body="before",
    created_at=None,
    updated_at=None,
    pinned=True,
  )

  async def update(_cls, block_id, patch, *, attachment_ids=None):
    assert attachment_ids is None
    assert patch.model_fields_set == {"body"}
    return SolvedMemo(block_id=block_id, canonical=patch.apply(original))

  monkeypatch.setattr(MemoApplicationService, "update", classmethod(update))
  response = client.patch(
    "/memos/api/v1/memos/17",
    headers={"Authorization": f"Bearer {PAT}"},
    params={"updateMask": "content"},
    json={"content": "after", "pinned": False},
  )

  assert response.status_code == 200
  assert response.json()["content"] == "after"
  assert response.json()["pinned"] is True


def test_unknown_memo_update_returns_404(monkeypatch):
  _, _, client = _publish({"personal_access_token": PAT})

  async def update(_cls, block_id, patch, *, attachment_ids=None):
    assert attachment_ids is None
    raise MemoNotFoundError(f"Memo memos/{block_id} not found")

  monkeypatch.setattr(MemoApplicationService, "update", classmethod(update))
  response = client.patch(
    "/memos/api/v1/memos/999",
    headers={"Authorization": f"Bearer {PAT}"},
    json={"content": "after"},
  )

  assert response.status_code == 404


@pytest.mark.parametrize(
  "body",
  [
    {"content": "x", "unknown": True},
    {"content": "x", "createTime": "2026-08-01T08:00:00"},
    {"content": "x", "attachments": [{"name": "attachments/020"}]},
  ],
)
def test_invalid_or_not_yet_supported_create_is_400_before_primary_write(
  monkeypatch,
  body,
):
  _, _, client = _publish({"personal_access_token": PAT})
  called = False

  async def create(_cls, canonical, *, attachment_ids=()):
    nonlocal called
    called = True
    return SolvedMemo(block_id=17, canonical=canonical)

  monkeypatch.setattr(MemoApplicationService, "create", classmethod(create))

  response = client.post(
    "/memos/api/v1/memos",
    headers={"Authorization": f"Bearer {PAT}"},
    json=body,
  )

  assert response.status_code == 400
  assert not called


def test_runtime_pat_replace_and_revoke_take_effect_without_route_rebuild():
  _, _, client = _publish({"personal_access_token": PAT})

  Extension.update_config(MemosConfig(personal_access_token=NEW_PAT))
  assert (
    client.get(
      "/memos/api/v1/auth/me",
      headers={"Authorization": f"Bearer {PAT}"},
    ).status_code
    == 401
  )
  assert (
    client.get(
      "/memos/api/v1/auth/me",
      headers={"Authorization": f"Bearer {NEW_PAT}"},
    ).status_code
    == 200
  )

  Extension.update_config(MemosConfig(personal_access_token=None))
  assert (
    client.get(
      "/memos/api/v1/auth/me",
      headers={"Authorization": f"Bearer {NEW_PAT}"},
    ).status_code
    == 401
  )
  assert client.get("/memos/api/v1/instance/profile").status_code == 200


def test_disable_and_reenable_replace_only_the_owned_route_set():
  app, mount, client = _publish({"personal_access_token": PAT})
  app.get("/core-proof")(lambda: {"ok": True})

  mount.unpublish()
  assert client.get("/memos/api/v1/instance/profile").status_code == 404
  assert client.get("/core-proof").status_code == 200

  replacement = ExtensionRouteMount(
    app,
    Extension.on_start(
      ExtensionModel(
        id="memos",
        version="0.1.0",
        enabled=[],
        config={"personal_access_token": PAT},
      )
    ),
  )
  replacement.publish()
  assert client.get("/memos/api/v1/instance/profile").status_code == 200
  assert list(app.openapi()["paths"]).count("/memos/api/v1/instance/profile") == 1


@pytest.mark.parametrize(
  "value",
  ["memos_pat_short", "wrong_" + "A" * 32, "memos_pat_" + "-" * 32],
)
def test_pat_config_rejects_non_0291_format(value):
  with pytest.raises(ValueError):
    MemosConfig(personal_access_token=value)
