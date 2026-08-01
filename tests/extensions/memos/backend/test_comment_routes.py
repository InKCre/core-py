"""Pinned Memos comment and ordinary memo deletion routes."""

import datetime
import json
from pathlib import Path

import fastapi
from fastapi.testclient import TestClient

from app.business.extension.routing import ExtensionRouteMount
from app.schemas.extension import ExtensionModel
from extensions.memos import Extension
from extensions.memos.family import (
  CanonicalMemo,
  CommentPage,
  MemoApplicationService,
  MemoNotFoundError,
  MemoVisibility,
  SolvedMemo,
)


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


def _headers() -> dict[str, str]:
  return {"Authorization": f"Bearer {PAT}"}


def _comment(block_id: int = 18) -> SolvedMemo:
  return SolvedMemo(
    block_id=block_id,
    canonical=CanonicalMemo(
      body="A reply",
      created_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
      updated_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
      visibility=MemoVisibility.PRIVATE,
    ),
    parent_id=17,
  )


def test_create_comment_returns_parent_from_resolved_graph(monkeypatch):
  client = _publish()

  async def create_comment(_cls, parent_id, canonical, *, attachment_ids):
    assert parent_id == 17
    assert canonical.body == "A reply"
    assert canonical.visibility is MemoVisibility.PUBLIC
    assert attachment_ids == ()
    return _comment()

  monkeypatch.setattr(
    MemoApplicationService,
    "create_comment",
    classmethod(create_comment),
  )
  response = client.post(
    "/memos/api/v1/memos/17/comments",
    headers=_headers(),
    json={
      "content": "A reply",
      "visibility": "PUBLIC",
      "attachments": [],
      "createTime": "2026-08-01T08:00:00Z",
    },
  )

  assert response.status_code == 200
  assert response.json() == json.loads(
    (FIXTURES / "create_comment_response.json").read_text(encoding="utf-8")
  )


def test_comment_list_token_is_parent_bound(monkeypatch):
  client = _publish()
  calls: list[tuple[int, int, int | None]] = []

  async def list_comments(_cls, parent_id, *, limit, after_block_id=None):
    calls.append((parent_id, limit, after_block_id))
    return CommentPage(
      comments=(_comment(),),
      next_block_id=18 if after_block_id is None else None,
      total_size=2,
    )

  monkeypatch.setattr(
    MemoApplicationService,
    "list_comments",
    classmethod(list_comments),
  )
  first = client.get(
    "/memos/api/v1/memos/17/comments",
    headers=_headers(),
    params={"pageSize": "1"},
  )
  token = first.json()["nextPageToken"]
  second = client.get(
    "/memos/api/v1/memos/17/comments",
    headers=_headers(),
    params={"pageSize": "1", "pageToken": token},
  )
  foreign = client.get(
    "/memos/api/v1/memos/19/comments",
    headers=_headers(),
    params={"pageSize": "1", "pageToken": token},
  )

  assert first.status_code == 200
  assert first.json()["totalSize"] == 2
  assert first.json()["memos"][0]["parent"] == "memos/17"
  assert second.status_code == 200
  assert calls == [(17, 1, None), (17, 1, 18)]
  assert foreign.status_code == 400


def test_delete_memo_uses_ordinary_resource_path_and_unknown_is_404(monkeypatch):
  client = _publish()
  deleted: list[int] = []

  def delete(_cls, block_id):
    if block_id == 999:
      raise MemoNotFoundError("missing")
    deleted.append(block_id)

  monkeypatch.setattr(MemoApplicationService, "delete", classmethod(delete))

  removed = client.delete("/memos/api/v1/memos/18", headers=_headers())
  missing = client.delete("/memos/api/v1/memos/999", headers=_headers())
  unsupported = client.delete(
    "/memos/api/v1/memos/18",
    headers=_headers(),
    params={"force": "true"},
  )

  assert removed.status_code == 200
  assert removed.json() == {}
  assert deleted == [18]
  assert missing.status_code == 404
  assert unsupported.status_code == 400
