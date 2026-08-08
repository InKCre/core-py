"""Opt-in proof against the declared PostgreSQL development contract."""

import asyncio
import datetime
import os
from pathlib import Path

import fastapi
from fastapi.testclient import TestClient
import pytest
import sqlalchemy
import sqlmodel

from app.business.info_base.block import BlockManager
from app.business.extension.routing import ExtensionRouteMount
from app.business.info_base.relation import RelationManager
from app.business.info_base.storage import StorageManager
from app.business.info_base.storage.postgresql import PostgreSQLBlobPointer
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel
from app.schemas.info_base.storage import StorageBlobModel
from app.schemas.extension import ExtensionModel
from extensions.memos import Extension
from extensions.memos.family import (
  AttachmentApplicationService,
  CanonicalMemo,
  CanonicalMemoPatch,
  MemoApplicationService,
  MemoVisibility,
)
from extensions.memos.family.attachment import AttachmentGraphRepository


pytestmark = pytest.mark.skipif(
  not os.getenv("INKCRE_TEST_DATABASE_URL"),
  reason="requires an explicitly selected migrated PostgreSQL runtime",
)

SEMANTIC_ASSETS = Path(__file__).parents[3] / "assets" / "semantic-content"


@pytest.fixture(scope="module", autouse=True)
def _generated_semantic_content_assets(semantic_content_assets: Path) -> None:
  assert semantic_content_assets == SEMANTIC_ASSETS


def _cleanup(tracked_block_ids: set[int], tracked_blob_ids: set) -> None:
  with SessionLocal() as db_session:
    for relation in db_session.exec(
      sqlmodel.select(RelationModel).where(
        sqlalchemy.or_(
          RelationModel.from_.in_(  # pyrefly: ignore[missing-attribute]
            tracked_block_ids
          ),
          RelationModel.to_.in_(  # pyrefly: ignore[missing-attribute]
            tracked_block_ids
          ),
        )
      )
    ).all():
      db_session.delete(relation)
    for block in db_session.exec(
      sqlmodel.select(BlockModel).where(
        BlockModel.id.in_(  # pyrefly: ignore[missing-attribute]
          tracked_block_ids
        )
      )
    ).all():
      db_session.delete(block)
    for blob in db_session.exec(
      sqlmodel.select(StorageBlobModel).where(
        StorageBlobModel.id.in_(  # pyrefly: ignore[missing-attribute]
          tracked_blob_ids
        )
      )
    ).all():
      db_session.delete(blob)
    db_session.commit()


def _track_attachment(solved, tracked_block_ids: set[int], tracked_blob_ids: set):
  tracked_block_ids.update((solved.block_id, solved.content_block_id))
  with SessionLocal() as db_session:
    content_block = BlockManager.get(solved.content_block_id, db_session)
    assert content_block is not None
    pointer = PostgreSQLBlobPointer.model_validate_json(content_block.content)
  tracked_blob_ids.add(pointer.blob_id)
  return pointer.blob_id


def _client(*, raise_server_exceptions: bool = True) -> TestClient:
  app = fastapi.FastAPI()
  model = ExtensionModel(
    id="memos",
    version="0.1.0",
    enabled=[],
    config={"personal_access_token": "memos_pat_" + "A" * 32},
  )
  mount = ExtensionRouteMount(app, Extension.on_start(model))
  mount.publish()
  return TestClient(app, raise_server_exceptions=raise_server_exceptions)


@pytest.mark.parametrize(
  ("filename", "media_type", "resolver_id"),
  (
    ("image.png", "image/png", "core.image.v1"),
    ("audio.wav", "audio/wav", "core.audio.v1"),
    ("video.mp4", "video/mp4", "core.video.v1"),
    ("document.pdf", "application/pdf", "core.pdf.v1"),
    ("book.epub", "application/epub+zip", "core.epub.v1"),
    ("archive.zip", "application/zip", "core.zip.v1"),
    ("unknown.bin", "application/x-inkcre-unknown", "core.file.v1"),
  ),
)
def test_memos_declared_media_type_selects_exact_semantic_content(
  filename,
  media_type,
  resolver_id,
):
  Extension._init_resolvers()
  StorageManager.setup_builtin_storages()
  tracked_block_ids: set[int] = set()
  tracked_blob_ids = set()

  try:
    solved = asyncio.run(
      AttachmentApplicationService.create(
        filename=filename,
        media_type=media_type,
        content=(SEMANTIC_ASSETS / filename).read_bytes(),
      )
    )
    _track_attachment(solved, tracked_block_ids, tracked_blob_ids)
    with SessionLocal() as db_session:
      metadata = BlockManager.get(solved.block_id, db_session)
      semantic = BlockManager.get(solved.content_block_id, db_session)
      assert metadata is not None and semantic is not None
      assert metadata.storage is None
      assert semantic.resolver == resolver_id
      assert semantic.storage == -4
      assert (
        RelationManager.get(
          solved.block_id,
          include_in=False,
          include_out=True,
          content="content",
          db_session=db_session,
        )[0].to_
        == solved.content_block_id
      )
    assert asyncio.run(
      AttachmentApplicationService.download(solved.block_id, filename)
    ) == (media_type, (SEMANTIC_ASSETS / filename).read_bytes())
  finally:
    _cleanup(tracked_block_ids, tracked_blob_ids)


def test_orphan_attach_reorder_download_and_owned_removal_round_trip():
  Extension._init_resolvers()
  StorageManager.setup_builtin_storages()
  tracked_block_ids: set[int] = set()
  tracked_blob_ids = set()

  try:
    first = asyncio.run(
      AttachmentApplicationService.create(
        filename="first.png",
        media_type="image/png",
        content=b"first",
      )
    )
    second = asyncio.run(
      AttachmentApplicationService.create(
        filename="second.png",
        media_type="image/png",
        content=b"second",
      )
    )
    first_blob_id = _track_attachment(first, tracked_block_ids, tracked_blob_ids)
    second_blob_id = _track_attachment(second, tracked_block_ids, tracked_blob_ids)

    memo = asyncio.run(
      MemoApplicationService.create(
        CanonicalMemo(
          body="attachment proof",
          created_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
          updated_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
        ),
        attachment_ids=(first.block_id, second.block_id),
      )
    )
    tracked_block_ids.add(memo.block_id)
    assert memo.attachment_ids == (first.block_id, second.block_id)
    assert asyncio.run(
      AttachmentApplicationService.download(first.block_id, "first.png")
    ) == ("image/png", b"first")

    reordered = asyncio.run(
      MemoApplicationService.update(
        memo.block_id,
        CanonicalMemoPatch(body="attachment proof updated"),
        attachment_ids=(second.block_id, first.block_id),
      )
    )
    assert reordered.attachment_ids == (second.block_id, first.block_id)

    reduced = asyncio.run(
      MemoApplicationService.update(
        memo.block_id,
        None,
        attachment_ids=(second.block_id,),
      )
    )
    assert reduced.attachment_ids == (second.block_id,)

    with SessionLocal() as db_session:
      assert BlockManager.get(first.block_id, db_session) is None
      assert db_session.get(StorageBlobModel, first_blob_id) is None
      remaining_relations = tuple(
        db_session.exec(
          sqlmodel.select(RelationModel).where(
            RelationModel.from_ == memo.block_id,
            RelationModel.content.like(  # pyrefly: ignore[missing-attribute]
              "attachment:%"
            ),
          )
        ).all()
      )
      assert [(relation.content, relation.to_) for relation in remaining_relations] == [
        ("attachment:0", second.block_id)
      ]

    AttachmentApplicationService.delete(second.block_id)
    with SessionLocal() as db_session:
      assert BlockManager.get(second.block_id, db_session) is None
      assert db_session.get(StorageBlobModel, second_blob_id) is None
  finally:
    _cleanup(tracked_block_ids, tracked_blob_ids)


def test_comment_visibility_and_owned_delete_preserve_shared_reference_targets():
  Extension._init_resolvers()
  StorageManager.setup_builtin_storages()
  tracked_block_ids: set[int] = set()
  tracked_blob_ids = set()

  async def attachment(name: str, content: bytes):
    solved = await AttachmentApplicationService.create(
      filename=name,
      media_type="image/png",
      content=content,
    )
    _track_attachment(solved, tracked_block_ids, tracked_blob_ids)
    return solved

  def canonical(body: str, visibility=MemoVisibility.PRIVATE):
    return CanonicalMemo(
      body=body,
      created_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
      updated_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
      visibility=visibility,
    )

  try:
    exclusive = asyncio.run(attachment("exclusive.png", b"exclusive"))
    shared = asyncio.run(attachment("shared.png", b"shared"))
    comment_owned = asyncio.run(attachment("comment.png", b"comment"))
    exclusive_blob_id = PostgreSQLBlobPointer.model_validate_json(
      BlockManager.get(exclusive.content_block_id).content  # type: ignore[union-attr]
    ).blob_id
    shared_blob_id = PostgreSQLBlobPointer.model_validate_json(
      BlockManager.get(shared.content_block_id).content  # type: ignore[union-attr]
    ).blob_id
    comment_blob_id = PostgreSQLBlobPointer.model_validate_json(
      BlockManager.get(comment_owned.content_block_id).content  # type: ignore[union-attr]
    ).blob_id

    target = asyncio.run(MemoApplicationService.create(canonical("target")))
    tracked_block_ids.add(target.block_id)
    parent = asyncio.run(
      MemoApplicationService.create(
        canonical("parent", MemoVisibility.PROTECTED),
        attachment_ids=(exclusive.block_id, shared.block_id),
      )
    )
    tracked_block_ids.add(parent.block_id)

    comment = asyncio.run(
      MemoApplicationService.create_comment(
        parent.block_id,
        canonical("comment", MemoVisibility.PUBLIC),
        attachment_ids=(comment_owned.block_id,),
      )
    )
    tracked_block_ids.add(comment.block_id)
    assert comment.parent_id == parent.block_id
    assert comment.canonical.visibility is MemoVisibility.PROTECTED

    nested = asyncio.run(
      MemoApplicationService.create_comment(
        comment.block_id,
        canonical("nested"),
      )
    )
    tracked_block_ids.add(nested.block_id)
    sibling = asyncio.run(
      MemoApplicationService.create_comment(
        parent.block_id,
        canonical("sibling"),
      )
    )
    tracked_block_ids.add(sibling.block_id)

    updated = asyncio.run(
      MemoApplicationService.update(
        comment.block_id,
        CanonicalMemoPatch(
          body="comment updated",
          visibility=MemoVisibility.PUBLIC,
        ),
      )
    )
    assert updated.canonical.body == "comment updated"
    assert updated.canonical.visibility is MemoVisibility.PROTECTED

    page = asyncio.run(MemoApplicationService.list_comments(parent.block_id, limit=10))
    assert page.total_size == 2
    assert {item.block_id for item in page.comments} == {
      comment.block_id,
      sibling.block_id,
    }
    assert all(item.parent_id == parent.block_id for item in page.comments)

    MemoApplicationService.delete(sibling.block_id)
    with SessionLocal() as db_session:
      assert BlockManager.get(sibling.block_id, db_session) is None
      assert BlockManager.get(parent.block_id, db_session) is not None

    with SessionLocal() as db_session:
      RelationManager.create(
        parent.block_id,
        target.block_id,
        "reference",
        db_session,
      )
      RelationManager.create(
        target.block_id,
        shared.block_id,
        "attachment:0",
        db_session,
      )
      db_session.commit()

    MemoApplicationService.delete(parent.block_id)
    with SessionLocal() as db_session:
      assert BlockManager.get(parent.block_id, db_session) is None
      assert BlockManager.get(comment.block_id, db_session) is None
      assert BlockManager.get(nested.block_id, db_session) is None
      assert BlockManager.get(exclusive.block_id, db_session) is None
      assert BlockManager.get(comment_owned.block_id, db_session) is None
      assert db_session.get(StorageBlobModel, exclusive_blob_id) is None
      assert db_session.get(StorageBlobModel, comment_blob_id) is None

      assert BlockManager.get(target.block_id, db_session) is not None
      assert BlockManager.get(shared.block_id, db_session) is not None
      assert db_session.get(StorageBlobModel, shared_blob_id) is not None
      surviving_owner = RelationManager.get(
        target.block_id,
        include_in=False,
        include_out=True,
        content="attachment:0",
        db_session=db_session,
      )
      assert [(item.from_, item.to_) for item in surviving_owner] == [
        (target.block_id, shared.block_id)
      ]
  finally:
    _cleanup(tracked_block_ids, tracked_blob_ids)


def test_comment_http_round_trip_reads_committed_resolver_graph():
  Extension._init_resolvers()
  StorageManager.setup_builtin_storages()
  client = _client()
  headers = {"Authorization": "Bearer " + "memos_pat_" + "A" * 32}
  tracked_block_ids: set[int] = set()

  try:
    parent_response = client.post(
      "/memos/api/v1/memos",
      headers=headers,
      json={
        "content": "HTTP parent",
        "visibility": "PROTECTED",
        "createTime": "2026-08-01T08:00:00Z",
      },
    )
    assert parent_response.status_code == 200
    parent_id = int(parent_response.json()["name"].removeprefix("memos/"))
    tracked_block_ids.add(parent_id)

    comment_response = client.post(
      f"/memos/api/v1/memos/{parent_id}/comments",
      headers=headers,
      json={
        "content": "HTTP comment",
        "visibility": "PUBLIC",
        "createTime": "2026-08-01T08:01:00Z",
      },
    )
    assert comment_response.status_code == 200
    assert comment_response.json()["visibility"] == "PROTECTED"
    assert comment_response.json()["parent"] == f"memos/{parent_id}"
    comment_id = int(comment_response.json()["name"].removeprefix("memos/"))
    tracked_block_ids.add(comment_id)

    listed = client.get(
      f"/memos/api/v1/memos/{parent_id}/comments",
      headers=headers,
    )
    assert listed.status_code == 200
    assert [item["name"] for item in listed.json()["memos"]] == [f"memos/{comment_id}"]

    patched = client.patch(
      f"/memos/api/v1/memos/{comment_id}",
      headers=headers,
      json={"content": "HTTP comment updated", "visibility": "PUBLIC"},
    )
    assert patched.status_code == 200
    assert patched.json()["content"] == "HTTP comment updated"
    assert patched.json()["visibility"] == "PROTECTED"
    assert patched.json()["parent"] == f"memos/{parent_id}"

    removed = client.delete(
      f"/memos/api/v1/memos/{comment_id}",
      headers=headers,
    )
    assert removed.status_code == 200
    assert (
      client.get(
        f"/memos/api/v1/memos/{parent_id}/comments",
        headers=headers,
      ).json()["memos"]
      == []
    )
    with SessionLocal() as db_session:
      assert BlockManager.get(comment_id, db_session) is None
      assert BlockManager.get(parent_id, db_session) is not None
  finally:
    _cleanup(tracked_block_ids, set())


def test_primary_delete_succeeds_when_best_effort_attachment_cleanup_fails(
  monkeypatch,
):
  Extension._init_resolvers()
  StorageManager.setup_builtin_storages()
  tracked_block_ids: set[int] = set()
  tracked_blob_ids = set()

  try:
    attachment = asyncio.run(
      AttachmentApplicationService.create(
        filename="residue.png",
        media_type="image/png",
        content=b"residue",
      )
    )
    attachment_blob_id = _track_attachment(
      attachment,
      tracked_block_ids,
      tracked_blob_ids,
    )
    memo = asyncio.run(
      MemoApplicationService.create(
        CanonicalMemo(
          body="primary delete proof",
          created_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
          updated_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
        ),
        attachment_ids=(attachment.block_id,),
      )
    )
    tracked_block_ids.add(memo.block_id)

    def fail_cleanup(_cls, _attachment_id, _db_session):
      raise RuntimeError("injected cleanup failure")

    monkeypatch.setattr(
      AttachmentGraphRepository,
      "delete_component",
      classmethod(fail_cleanup),
    )
    MemoApplicationService.delete(memo.block_id)

    with SessionLocal() as db_session:
      assert BlockManager.get(memo.block_id, db_session) is None
      assert BlockManager.get(attachment.block_id, db_session) is not None
      assert db_session.get(StorageBlobModel, attachment_blob_id) is not None
  finally:
    _cleanup(tracked_block_ids, tracked_blob_ids)


def test_missing_raw_bytes_are_404_without_fabricating_attachment_success():
  Extension._init_resolvers()
  StorageManager.setup_builtin_storages()
  client = _client()
  headers = {"Authorization": "Bearer " + "memos_pat_" + "A" * 32}
  tracked_block_ids: set[int] = set()
  tracked_blob_ids = set()

  try:
    created = client.post(
      "/memos/api/v1/attachments",
      headers=headers,
      json={
        "filename": "missing.png",
        "type": "image/png",
        "content": "cmF3",
      },
    )
    assert created.status_code == 200
    attachment_id = int(created.json()["name"].removeprefix("attachments/"))
    tracked_block_ids.add(attachment_id)

    with SessionLocal() as db_session:
      metadata_block = BlockManager.get(attachment_id, db_session)
      assert metadata_block is not None
      content_block = AttachmentGraphRepository.content_block(attachment_id, db_session)
      assert content_block.id is not None
      tracked_block_ids.add(content_block.id)
      pointer = PostgreSQLBlobPointer.model_validate_json(content_block.content)
      tracked_blob_ids.add(pointer.blob_id)
      blob = db_session.get(StorageBlobModel, pointer.blob_id)
      assert blob is not None
      db_session.delete(blob)
      db_session.commit()

    missing = client.get(
      f"/memos/file/attachments/{attachment_id}/missing.png",
      headers=headers,
    )
    assert missing.status_code == 404
    with SessionLocal() as db_session:
      assert BlockManager.get(attachment_id, db_session) is not None
  finally:
    _cleanup(tracked_block_ids, tracked_blob_ids)


def test_unknown_component_resolver_returns_500_instead_of_partial_memo_success():
  Extension._init_resolvers()
  StorageManager.setup_builtin_storages()
  client = _client(raise_server_exceptions=False)
  headers = {"Authorization": "Bearer " + "memos_pat_" + "A" * 32}
  tracked_block_ids: set[int] = set()

  try:
    memo = asyncio.run(
      MemoApplicationService.create(
        CanonicalMemo(
          body="unknown resolver proof",
          created_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
          updated_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
        )
      )
    )
    tracked_block_ids.add(memo.block_id)
    with SessionLocal() as db_session:
      unknown = BlockManager.create(
        BlockModel(
          resolver="extensions.memos.unknown.future",
          content="opaque",
        ),
        db_session,
      )
      assert unknown.id is not None
      tracked_block_ids.add(unknown.id)
      RelationManager.create(
        memo.block_id,
        unknown.id,
        "attachment:0",
        db_session,
      )
      db_session.commit()

    response = client.get(
      "/memos/api/v1/memos",
      headers=headers,
      params={"filter": 'creator == "users/inkcre"'},
    )
    assert response.status_code == 500
  finally:
    _cleanup(tracked_block_ids, set())
