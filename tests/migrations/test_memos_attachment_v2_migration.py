"""Online data-preservation proof for the Memos attachment v2 migration."""

import asyncio
import datetime
import json
import os
from pathlib import Path
import uuid

from alembic import command
from alembic.config import Config
import pytest
import sqlalchemy
import sqlmodel

from app.business.info_base.block import BlockManager
from app.business.info_base.relation import RelationManager
from app.business.info_base.storage.postgresql import PostgreSQLBlobPointer
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel
from app.schemas.info_base.storage import StorageBlobModel
from extensions.memos import Extension
from extensions.memos.family import AttachmentApplicationService, CanonicalAttachment


pytestmark = pytest.mark.skipif(
  not os.getenv("INKCRE_TEST_DATABASE_URL"),
  reason="requires an explicitly selected migrated PostgreSQL runtime",
)

PROJECT_ROOT = Path(__file__).parents[2]
V1 = "extensions.memos.attachment.v1"
V2 = "extensions.memos.attachment.v2"
PREVIOUS_REVISION = "d0e3f4a5b6c7"


def _alembic() -> Config:
  config = Config(PROJECT_ROOT / "alembic.ini")
  config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
  return config


def _cleanup(block_ids: set[int], blob_ids: set[uuid.UUID]) -> None:
  with SessionLocal() as db_session:
    for relation in db_session.exec(
      sqlmodel.select(RelationModel).where(
        sqlalchemy.or_(
          RelationModel.from_.in_(block_ids),  # pyrefly: ignore[missing-attribute]
          RelationModel.to_.in_(block_ids),  # pyrefly: ignore[missing-attribute]
        )
      )
    ).all():
      db_session.delete(relation)
    for block_id in block_ids:
      if (block := db_session.get(BlockModel, block_id)) is not None:
        db_session.delete(block)
    for blob_id in blob_ids:
      if (blob := db_session.get(StorageBlobModel, blob_id)) is not None:
        db_session.delete(blob)
    db_session.commit()


def test_seeded_v1_upgrade_and_downgrade_preserve_identity_blob_and_owner_slot():
  config = _alembic()
  block_ids: set[int] = set()
  blob_ids: set[uuid.UUID] = set()
  command.downgrade(config, PREVIOUS_REVISION)

  try:
    with SessionLocal() as db_session:
      blob = StorageBlobModel(data=b"migration bytes")
      db_session.add(blob)
      db_session.flush()
      blob_ids.add(blob.id)
      memo = BlockModel(resolver="extensions.memos.memo.v1", content="{}")
      db_session.add(memo)
      db_session.flush()
      canonical_v1 = {
        "filename": "migration.png",
        "media_type": "image/png",
        "size": len(blob.data),
        "created_at": "2026-08-01T08:00:00Z",
        "blob_id": str(blob.id),
      }
      attachment = BlockModel(
        resolver=V1,
        storage=-4,
        content=json.dumps(canonical_v1, separators=(",", ":")),
      )
      db_session.add(attachment)
      db_session.flush()
      assert memo.id is not None and attachment.id is not None
      block_ids.update((memo.id, attachment.id))
      relation = RelationModel(
        from_=memo.id,
        to_=attachment.id,
        content="attachment:0",
      )
      db_session.add(relation)
      db_session.commit()
      attachment_id = attachment.id
      memo_id = memo.id
      blob_id = blob.id

    command.upgrade(config, "head")
    Extension._init_resolvers()
    with SessionLocal() as db_session:
      metadata = BlockManager.get(attachment_id, db_session)
      assert metadata is not None
      assert metadata.resolver == V2
      assert metadata.storage is None
      canonical = CanonicalAttachment.from_block_content(metadata.content)
      assert canonical.filename == "migration.png"
      content_relations = RelationManager.get(
        attachment_id,
        include_in=False,
        include_out=True,
        content="content",
        db_session=db_session,
      )
      assert len(content_relations) == 1
      semantic_id = content_relations[0].to_
      block_ids.add(semantic_id)
      semantic = BlockManager.get(semantic_id, db_session)
      assert semantic is not None
      assert semantic.resolver == "core.image.v1"
      assert semantic.storage == -4
      assert PostgreSQLBlobPointer.model_validate_json(semantic.content).blob_id == blob_id
      owner = RelationManager.get(
        memo_id,
        include_in=False,
        include_out=True,
        content="attachment:0",
        db_session=db_session,
      )
      assert [(item.from_, item.to_) for item in owner] == [(memo_id, attachment_id)]
    assert asyncio.run(
      AttachmentApplicationService.download(attachment_id, "migration.png")
    ) == ("image/png", b"migration bytes")

    command.downgrade(config, PREVIOUS_REVISION)
    with SessionLocal() as db_session:
      metadata = BlockManager.get(attachment_id, db_session)
      assert metadata is not None
      assert metadata.resolver == V1
      assert metadata.storage == -4
      restored = json.loads(metadata.content)
      assert restored["blob_id"] == str(blob_id)
      assert db_session.get(StorageBlobModel, blob_id).data == b"migration bytes"  # type: ignore[union-attr]
      assert BlockManager.get(semantic_id, db_session) is None
      assert (
        RelationManager.get(
          attachment_id,
          include_in=False,
          include_out=True,
          content="content",
          db_session=db_session,
        )
        == ()
      )
      owner = RelationManager.get(
        memo_id,
        include_in=False,
        include_out=True,
        content="attachment:0",
        db_session=db_session,
      )
      assert [(item.from_, item.to_) for item in owner] == [(memo_id, attachment_id)]
  finally:
    _cleanup(block_ids, blob_ids)
    command.upgrade(config, "head")


def test_downgrade_refuses_shared_semantic_content_before_mutation():
  config = _alembic()
  block_ids: set[int] = set()
  blob_ids: set[uuid.UUID] = set()

  try:
    with SessionLocal() as db_session:
      blob = StorageBlobModel(data=b"shared")
      db_session.add(blob)
      db_session.flush()
      blob_ids.add(blob.id)
      semantic = BlockModel(
        resolver="core.file.v1",
        storage=-4,
        content=PostgreSQLBlobPointer(blob_id=blob.id).model_dump_json(),
      )
      db_session.add(semantic)
      db_session.flush()
      canonical = CanonicalAttachment(
        filename="shared.bin",
        media_type="application/octet-stream",
        size=6,
        created_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
      )
      metadata = [
        BlockModel(resolver=V2, content=canonical.to_block_content()),
        BlockModel(resolver=V2, content=canonical.to_block_content()),
      ]
      db_session.add_all(metadata)
      db_session.flush()
      assert semantic.id is not None and all(item.id is not None for item in metadata)
      for item in metadata:
        db_session.add(RelationModel(from_=item.id, to_=semantic.id, content="content"))
      db_session.commit()
      metadata_ids = tuple(item.id for item in metadata if item.id is not None)
      block_ids.update((semantic.id, *metadata_ids))

    with pytest.raises(RuntimeError, match="post-upgrade information"):
      command.downgrade(config, PREVIOUS_REVISION)

    with SessionLocal() as db_session:
      assert all(
        db_session.get(BlockModel, item_id) is not None for item_id in metadata_ids
      )
      assert db_session.get(BlockModel, semantic.id) is not None
  finally:
    _cleanup(block_ids, blob_ids)
    command.upgrade(config, "head")
