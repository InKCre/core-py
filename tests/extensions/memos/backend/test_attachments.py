"""Memos 0.29.1 attachment journey and auth contract."""

import datetime
import json
from pathlib import Path

import fastapi
from fastapi.testclient import TestClient
import pytest

from app.business.extension.routing import ExtensionRouteMount
from app.schemas.extension import ExtensionModel
from extensions.memos import Extension
from extensions.memos.family import (
  AttachmentApplicationService,
  AttachmentNotFoundError,
  CanonicalAttachment,
  CanonicalMemo,
  MemoApplicationService,
  SolvedAttachment,
  SolvedMemo,
)
from extensions.memos.products.memos.v0_29_1 import backend


PAT = "memos_pat_" + "A" * 32
FIXTURES = Path(__file__).parents[1] / "products" / "memos" / "v0_29_1" / "fixtures"


def _publish() -> TestClient:
  app = fastapi.FastAPI()
  model = ExtensionModel(
    id="memos",
    version="0.1.0",
    enabled=[],
    config={"personal_access_token": PAT},
  )
  mount = ExtensionRouteMount(app, Extension.on_start(model))
  mount.publish()
  return TestClient(app)


def _attachment(
  block_id: int = 23,
  *,
  filename: str = "photo.png",
  owner_memo_id: int | None = None,
) -> SolvedAttachment:
  return SolvedAttachment(
    block_id=block_id,
    content_block_id=block_id + 100,
    canonical=CanonicalAttachment(
      filename=filename,
      media_type="image/png",
      size=3,
      created_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
    ),
    owner_memo_id=owner_memo_id,
  )


def _headers() -> dict[str, str]:
  return {"Authorization": f"Bearer {PAT}"}


def test_orphan_upload_matches_fixture_and_passes_decoded_bytes(monkeypatch):
  client = _publish()
  fixture = json.loads((FIXTURES / "create_attachment.json").read_text(encoding="utf-8"))

  async def create(_cls, **kwargs):
    assert kwargs == {
      "filename": "photo.png",
      "media_type": "image/png",
      "content": b"PNG",
      "memo_id": None,
    }
    return _attachment()

  monkeypatch.setattr(AttachmentApplicationService, "create", classmethod(create))

  response = client.post(
    "/memos/api/v1/attachments",
    headers=_headers(),
    json=fixture,
  )

  assert response.status_code == 200
  assert response.json() == json.loads(
    (FIXTURES / "create_attachment_response.json").read_text(encoding="utf-8")
  )


def test_attachment_upload_accepts_an_exact_memo_owner(monkeypatch):
  client = _publish()

  async def create(_cls, **kwargs):
    assert kwargs["memo_id"] == 17
    return _attachment(owner_memo_id=17)

  monkeypatch.setattr(AttachmentApplicationService, "create", classmethod(create))
  response = client.post(
    "/memos/api/v1/attachments",
    headers=_headers(),
    json={
      "filename": "photo.png",
      "type": "image/png",
      "content": "UE5H",
      "memo": "memos/17",
    },
  )

  assert response.status_code == 200
  assert response.json()["memo"] == "memos/17"


@pytest.mark.parametrize(
  "payload",
  [
    {"filename": "../photo.png", "type": "image/png", "content": "UE5H"},
    {"filename": "photo.png", "type": "not-a-media-type", "content": "UE5H"},
    {"filename": "photo.png", "type": "image/png", "content": "***"},
    {
      "filename": "photo.png",
      "type": "image/png",
      "content": "UE5H",
      "memo": "wrong/17",
    },
  ],
)
def test_invalid_upload_is_rejected_before_storage(monkeypatch, payload):
  client = _publish()
  called = False

  async def create(_cls, **_kwargs):
    nonlocal called
    called = True
    return _attachment()

  monkeypatch.setattr(AttachmentApplicationService, "create", classmethod(create))

  response = client.post(
    "/memos/api/v1/attachments",
    headers=_headers(),
    json=payload,
  )

  assert response.status_code == 400
  assert not called


def test_decoded_size_cap_returns_413_before_storage(monkeypatch):
  client = _publish()
  monkeypatch.setattr(backend, "MAX_ATTACHMENT_BYTES", 2)
  called = False

  async def create(_cls, **_kwargs):
    nonlocal called
    called = True
    return _attachment()

  monkeypatch.setattr(AttachmentApplicationService, "create", classmethod(create))
  response = client.post(
    "/memos/api/v1/attachments",
    headers=_headers(),
    json={"filename": "photo.png", "type": "image/png", "content": "UE5H"},
  )

  assert backend.MAX_ATTACHMENT_REQUEST_BYTES > 32 * 1024 * 1024
  assert response.status_code == 413
  assert not called


def test_list_download_and_delete_share_pat_and_application_service(monkeypatch):
  client = _publish()
  deleted: list[int] = []

  async def list_(_cls):
    return (_attachment(),)

  async def download(_cls, attachment_id, filename):
    assert (attachment_id, filename) == (23, "photo.png")
    return "image/png", b"PNG"

  def delete(_cls, attachment_id):
    deleted.append(attachment_id)

  monkeypatch.setattr(AttachmentApplicationService, "list", classmethod(list_))
  monkeypatch.setattr(
    AttachmentApplicationService,
    "download",
    classmethod(download),
  )
  monkeypatch.setattr(AttachmentApplicationService, "delete", classmethod(delete))

  assert client.get("/memos/api/v1/attachments").status_code == 401
  assert client.get("/memos/file/attachments/23/photo.png").status_code == 401

  listed = client.get("/memos/api/v1/attachments", headers=_headers())
  downloaded = client.get(
    "/memos/file/attachments/23/photo.png",
    headers=_headers(),
  )
  removed = client.delete("/memos/api/v1/attachments/23", headers=_headers())

  assert [item["name"] for item in listed.json()["attachments"]] == ["attachments/23"]
  assert downloaded.content == b"PNG"
  assert downloaded.headers["content-type"] == "image/png"
  assert removed.status_code == 200
  assert removed.json() == {}
  assert deleted == [23]


def test_missing_attachment_maps_to_404(monkeypatch):
  client = _publish()

  async def download(_cls, _attachment_id, _filename):
    raise AttachmentNotFoundError("missing")

  monkeypatch.setattr(
    AttachmentApplicationService,
    "download",
    classmethod(download),
  )

  assert (
    client.get(
      "/memos/file/attachments/999/missing.png",
      headers=_headers(),
    ).status_code
    == 404
  )


def test_create_and_patch_pass_ordered_attachment_sets(monkeypatch):
  client = _publish()
  canonical = CanonicalMemo(
    body="x",
    created_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
    updated_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
  )

  async def create(_cls, _canonical, *, attachment_ids):
    assert attachment_ids == (23, 24)
    return SolvedMemo(
      block_id=17,
      canonical=canonical,
      attachments=(
        _attachment(23, owner_memo_id=17),
        _attachment(24, filename="second.png", owner_memo_id=17),
      ),
    )

  async def update(_cls, block_id, patch, *, attachment_ids):
    assert block_id == 17
    assert patch is None
    assert attachment_ids == (24, 23)
    return SolvedMemo(
      block_id=17,
      canonical=canonical,
      attachments=(
        _attachment(24, filename="second.png", owner_memo_id=17),
        _attachment(23, owner_memo_id=17),
      ),
    )

  monkeypatch.setattr(MemoApplicationService, "create", classmethod(create))
  created = client.post(
    "/memos/api/v1/memos",
    headers=_headers(),
    json={
      "content": "x",
      "attachments": [
        {"name": "attachments/23"},
        {"name": "attachments/24"},
      ],
      "createTime": "2026-08-01T08:00:00Z",
    },
  )
  assert [item["name"] for item in created.json()["attachments"]] == [
    "attachments/23",
    "attachments/24",
  ]

  monkeypatch.setattr(MemoApplicationService, "update", classmethod(update))
  updated = client.patch(
    "/memos/api/v1/memos/17",
    headers=_headers(),
    json={
      "attachments": [
        {"name": "attachments/24"},
        {"name": "attachments/23"},
      ]
    },
  )
  assert [item["name"] for item in updated.json()["attachments"]] == [
    "attachments/24",
    "attachments/23",
  ]
