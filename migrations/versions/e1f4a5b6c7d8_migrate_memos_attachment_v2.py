"""migrate Memos attachment metadata to v2 graph

Revision ID: e1f4a5b6c7d8
Revises: d0e3f4a5b6c7
Create Date: 2026-08-02

"""

from collections.abc import Sequence
import datetime
import json
import uuid

from alembic import op
import sqlalchemy as sa

from app.database_contract import PROTOCOL_SCHEMA


revision: str = "e1f4a5b6c7d8"
down_revision: str | Sequence[str] | None = "d0e3f4a5b6c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ATTACHMENT_V1 = "extensions.memos.attachment.v1"
_ATTACHMENT_V2 = "extensions.memos.attachment.v2"
_CONTENT_RELATION = "content"
_POSTGRESQL_STORAGE_ID = -4
_METADATA_FIELDS = ("filename", "media_type", "size", "created_at")
_CORE_RESOLVERS = {
  "core.text.v1",
  "core.html.v1",
  "core.image.v1",
  "core.audio.v1",
  "core.video.v1",
  "core.pdf.v1",
  "core.epub.v1",
  "core.zip.v1",
  "core.file.v1",
}


def _json(value: dict) -> str:
  return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _validate_timestamp(value: object) -> None:
  if not isinstance(value, str):
    raise RuntimeError("Memos attachment created_at must be an RFC3339 string")
  try:
    parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
  except ValueError as error:
    raise RuntimeError("Memos attachment created_at is invalid") from error
  if parsed.tzinfo is None or parsed.utcoffset() is None:
    raise RuntimeError("Memos attachment created_at must contain a timezone")


def _validate_metadata(value: object, *, v1: bool) -> tuple[dict, uuid.UUID | None]:
  if not isinstance(value, dict):
    raise RuntimeError("Memos attachment canonical content must be a JSON object")
  expected = set(_METADATA_FIELDS) | ({"blob_id"} if v1 else set())
  if set(value) != expected:
    raise RuntimeError("Memos attachment canonical content has unexpected fields")
  if not isinstance(value["filename"], str) or not isinstance(value["media_type"], str):
    raise RuntimeError("Memos attachment filename and media_type must be strings")
  if (
    isinstance(value["size"], bool)
    or not isinstance(value["size"], int)
    or value["size"] < 0
  ):
    raise RuntimeError("Memos attachment size must be a non-negative integer")
  _validate_timestamp(value["created_at"])
  metadata = {key: value[key] for key in _METADATA_FIELDS}
  if not v1:
    return metadata, None
  try:
    blob_id = uuid.UUID(str(value["blob_id"]))
  except (TypeError, ValueError, AttributeError) as error:
    raise RuntimeError("Memos attachment blob_id is invalid") from error
  return metadata, blob_id


def _resolver_for_media_type(media_type: str) -> str:
  normalized = media_type.partition(";")[0].strip().lower()
  exact = {
    "text/plain": "core.text.v1",
    "text/html": "core.html.v1",
    "application/xhtml+xml": "core.html.v1",
    "application/pdf": "core.pdf.v1",
    "application/epub+zip": "core.epub.v1",
    "application/zip": "core.zip.v1",
    "application/x-zip-compressed": "core.zip.v1",
  }
  if normalized in exact:
    return exact[normalized]
  family = normalized.partition("/")[0]
  return {
    "image": "core.image.v1",
    "audio": "core.audio.v1",
    "video": "core.video.v1",
  }.get(family, "core.file.v1")


def _load_json(content: str, block_id: int) -> object:
  try:
    return json.loads(content)
  except json.JSONDecodeError as error:
    raise RuntimeError(
      f"Memos attachment block {block_id} contains invalid JSON"
    ) from error


def upgrade() -> None:
  if op.get_context().as_sql:
    op.execute(
      f"""
      DO $$
      BEGIN
        IF EXISTS (
          SELECT 1 FROM "{PROTOCOL_SCHEMA}".blocks
          WHERE resolver = '{_ATTACHMENT_V1}'
        ) THEN
          RAISE EXCEPTION 'Memos attachment v1 data requires online migration';
        END IF;
      END
      $$
      """
    )
    return
  connection = op.get_bind()
  rows = connection.execute(
    sa.text(
      f"""
      SELECT id, storage, content
      FROM "{PROTOCOL_SCHEMA}".blocks
      WHERE resolver = :resolver
      ORDER BY id
      FOR UPDATE
      """
    ),
    {"resolver": _ATTACHMENT_V1},
  ).mappings()

  for row in rows:
    block_id = row["id"]
    if row["storage"] != _POSTGRESQL_STORAGE_ID:
      raise RuntimeError(
        f"Memos attachment block {block_id} does not use PostgreSQL storage"
      )
    metadata, blob_id = _validate_metadata(
      _load_json(row["content"], block_id),
      v1=True,
    )
    assert blob_id is not None
    if (
      connection.execute(
        sa.text(f'SELECT 1 FROM "{PROTOCOL_SCHEMA}".storage_blobs WHERE id = :blob_id'),
        {"blob_id": blob_id},
      ).first()
      is None
    ):
      raise RuntimeError(f"Memos attachment block {block_id} points to a missing blob")
    if (
      connection.execute(
        sa.text(
          f"""
        SELECT 1
        FROM "{PROTOCOL_SCHEMA}".relations
        WHERE from_ = :block_id AND content = :content
        """
        ),
        {"block_id": block_id, "content": _CONTENT_RELATION},
      ).first()
      is not None
    ):
      raise RuntimeError(f"Memos attachment block {block_id} already has content")

    semantic_id = connection.execute(
      sa.text(
        f"""
        INSERT INTO "{PROTOCOL_SCHEMA}".blocks
          (created_at, updated_at, storage, resolver, content)
        SELECT created_at, updated_at, :storage, :resolver, :content
        FROM "{PROTOCOL_SCHEMA}".blocks
        WHERE id = :block_id
        RETURNING id
        """
      ),
      {
        "storage": _POSTGRESQL_STORAGE_ID,
        "resolver": _resolver_for_media_type(metadata["media_type"]),
        "content": _json({"blob_id": str(blob_id)}),
        "block_id": block_id,
      },
    ).scalar_one()
    connection.execute(
      sa.text(
        f"""
        UPDATE "{PROTOCOL_SCHEMA}".blocks
        SET storage = NULL, resolver = :resolver, content = :content
        WHERE id = :block_id
        """
      ),
      {
        "resolver": _ATTACHMENT_V2,
        "content": _json(metadata),
        "block_id": block_id,
      },
    )
    connection.execute(
      sa.text(
        f"""
        INSERT INTO "{PROTOCOL_SCHEMA}".relations (from_, to_, content)
        VALUES (:from_id, :to_id, :content)
        """
      ),
      {"from_id": block_id, "to_id": semantic_id, "content": _CONTENT_RELATION},
    )


def downgrade() -> None:
  if op.get_context().as_sql:
    op.execute(
      f"""
      DO $$
      BEGIN
        IF EXISTS (
          SELECT 1 FROM "{PROTOCOL_SCHEMA}".blocks
          WHERE resolver = '{_ATTACHMENT_V2}'
        ) THEN
          RAISE EXCEPTION 'Memos attachment v2 data requires online downgrade';
        END IF;
      END
      $$
      """
    )
    return
  connection = op.get_bind()
  rows = list(
    connection.execute(
      sa.text(
        f"""
        SELECT id, storage, content
        FROM "{PROTOCOL_SCHEMA}".blocks
        WHERE resolver = :resolver
        ORDER BY id
        FOR UPDATE
        """
      ),
      {"resolver": _ATTACHMENT_V2},
    ).mappings()
  )
  plans: list[tuple[int, int, int, dict, uuid.UUID]] = []

  for row in rows:
    block_id = row["id"]
    if row["storage"] is not None:
      raise RuntimeError(f"Memos attachment block {block_id} v2 must be inline")
    metadata, _ = _validate_metadata(_load_json(row["content"], block_id), v1=False)
    relations = list(
      connection.execute(
        sa.text(
          f"""
          SELECT id, to_
          FROM "{PROTOCOL_SCHEMA}".relations
          WHERE from_ = :block_id AND content = :content
          FOR UPDATE
          """
        ),
        {"block_id": block_id, "content": _CONTENT_RELATION},
      ).mappings()
    )
    if len(relations) != 1:
      raise RuntimeError(
        f"Memos attachment block {block_id} does not have one reversible content relation"
      )
    relation_id = relations[0]["id"]
    semantic_id = relations[0]["to_"]
    semantic = (
      connection.execute(
        sa.text(
          f"""
        SELECT storage, resolver, content
        FROM "{PROTOCOL_SCHEMA}".blocks
        WHERE id = :semantic_id
        FOR UPDATE
        """
        ),
        {"semantic_id": semantic_id},
      )
      .mappings()
      .one_or_none()
    )
    if (
      semantic is None
      or semantic["storage"] != _POSTGRESQL_STORAGE_ID
      or semantic["resolver"] not in _CORE_RESOLVERS
    ):
      raise RuntimeError(f"Memos attachment block {block_id} has non-reversible content")
    pointer = _load_json(semantic["content"], semantic_id)
    if not isinstance(pointer, dict) or set(pointer) != {"blob_id"}:
      raise RuntimeError(f"Memos content block {semantic_id} has a non-minimal pointer")
    try:
      blob_id = uuid.UUID(str(pointer["blob_id"]))
    except (TypeError, ValueError, AttributeError) as error:
      raise RuntimeError(
        f"Memos content block {semantic_id} has an invalid pointer"
      ) from error
    if (
      connection.execute(
        sa.text(f'SELECT 1 FROM "{PROTOCOL_SCHEMA}".storage_blobs WHERE id = :blob_id'),
        {"blob_id": blob_id},
      ).first()
      is None
    ):
      raise RuntimeError(f"Memos content block {semantic_id} points to a missing blob")
    relation_count = connection.execute(
      sa.text(
        f"""
        SELECT count(*)
        FROM "{PROTOCOL_SCHEMA}".relations
        WHERE from_ = :semantic_id OR to_ = :semantic_id
        """
      ),
      {"semantic_id": semantic_id},
    ).scalar_one()
    embedding_count = connection.execute(
      sa.text(
        f"""
        SELECT count(*)
        FROM "{PROTOCOL_SCHEMA}".block_embeddings
        WHERE id = :semantic_id
        """
      ),
      {"semantic_id": semantic_id},
    ).scalar_one()
    if relation_count != 1 or embedding_count != 0:
      raise RuntimeError(f"Memos content block {semantic_id} owns post-upgrade information")
    plans.append((block_id, semantic_id, relation_id, metadata, blob_id))

  for block_id, semantic_id, relation_id, metadata, blob_id in plans:
    connection.execute(
      sa.text(f'DELETE FROM "{PROTOCOL_SCHEMA}".relations WHERE id = :relation_id'),
      {"relation_id": relation_id},
    )
    connection.execute(
      sa.text(f'DELETE FROM "{PROTOCOL_SCHEMA}".blocks WHERE id = :semantic_id'),
      {"semantic_id": semantic_id},
    )
    connection.execute(
      sa.text(
        f"""
        UPDATE "{PROTOCOL_SCHEMA}".blocks
        SET storage = :storage, resolver = :resolver, content = :content
        WHERE id = :block_id
        """
      ),
      {
        "storage": _POSTGRESQL_STORAGE_ID,
        "resolver": _ATTACHMENT_V1,
        "content": _json({**metadata, "blob_id": str(blob_id)}),
        "block_id": block_id,
      },
    )
