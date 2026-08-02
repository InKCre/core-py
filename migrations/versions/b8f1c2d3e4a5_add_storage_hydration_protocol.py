"""add storage hydration protocol

Revision ID: b8f1c2d3e4a5
Revises: f2c8a6d1e4b7
Create Date: 2026-08-02

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.database_contract import INTERNAL_SCHEMA, PROTOCOL_SCHEMA


revision: str = "b8f1c2d3e4a5"
down_revision: str | Sequence[str] | None = "f2c8a6d1e4b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.drop_constraint(
    "blocks_storage_fkey",
    "blocks",
    schema=PROTOCOL_SCHEMA,
    type_="foreignkey",
  )
  op.create_foreign_key(
    "blocks_storage_fkey",
    "blocks",
    "storages",
    ["storage"],
    ["id"],
    source_schema=PROTOCOL_SCHEMA,
    referent_schema=PROTOCOL_SCHEMA,
    onupdate="CASCADE",
    ondelete="RESTRICT",
  )

  op.execute(
    f"""
    CREATE FUNCTION "{PROTOCOL_SCHEMA}".create_storage_blob(bytea)
    RETURNS uuid
    LANGUAGE sql
    VOLATILE
    SECURITY INVOKER
    SET search_path = pg_catalog
    AS $$
      INSERT INTO "{PROTOCOL_SCHEMA}".storage_blobs (data)
      VALUES ($1)
      RETURNING id
    $$
    """
  )
  op.execute(
    f"""
    CREATE FUNCTION "{PROTOCOL_SCHEMA}".read_storage_blob(blob_id uuid)
    RETURNS bytea
    LANGUAGE plpgsql
    STABLE
    SECURITY INVOKER
    SET search_path = pg_catalog
    AS $$
    DECLARE
      stored_data bytea;
    BEGIN
      SELECT data
      INTO stored_data
      FROM "{PROTOCOL_SCHEMA}".storage_blobs
      WHERE id = $1;

      IF NOT FOUND THEN
        RAISE SQLSTATE 'PT404' USING MESSAGE = 'storage blob not found';
      END IF;

      RETURN stored_data;
    END
    $$
    """
  )
  op.execute(
    f'REVOKE ALL ON FUNCTION "{PROTOCOL_SCHEMA}".create_storage_blob(bytea) FROM PUBLIC'
  )
  op.execute(
    f'REVOKE ALL ON FUNCTION "{PROTOCOL_SCHEMA}".read_storage_blob(uuid) FROM PUBLIC'
  )
  op.execute(
    sa.text(
      f"""
      UPDATE "{INTERNAL_SCHEMA}".contract_state
      SET contract_revision = 'peer-database-runtime-v2',
          updated_at = CURRENT_TIMESTAMP
      WHERE singleton
      """
    )
  )


def downgrade() -> None:
  op.execute(
    sa.text(
      f"""
      UPDATE "{INTERNAL_SCHEMA}".contract_state
      SET contract_revision = 'peer-database-runtime-v1',
          updated_at = CURRENT_TIMESTAMP
      WHERE singleton
      """
    )
  )
  op.execute(f'DROP FUNCTION "{PROTOCOL_SCHEMA}".read_storage_blob(uuid)')
  op.execute(f'DROP FUNCTION "{PROTOCOL_SCHEMA}".create_storage_blob(bytea)')

  op.drop_constraint(
    "blocks_storage_fkey",
    "blocks",
    schema=PROTOCOL_SCHEMA,
    type_="foreignkey",
  )
  op.create_foreign_key(
    "blocks_storage_fkey",
    "blocks",
    "storages",
    ["storage"],
    ["id"],
    source_schema=PROTOCOL_SCHEMA,
    referent_schema=PROTOCOL_SCHEMA,
    onupdate="CASCADE",
    ondelete="SET NULL",
  )
