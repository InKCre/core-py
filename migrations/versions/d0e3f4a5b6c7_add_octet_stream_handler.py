"""add the PostgREST octet-stream response handler

Revision ID: d0e3f4a5b6c7
Revises: c9d2e3f4a5b6
Create Date: 2026-08-02

"""

from collections.abc import Sequence

from alembic import op

from app.database_contract import PROTOCOL_SCHEMA


revision: str = "d0e3f4a5b6c7"
down_revision: str | Sequence[str] | None = "c9d2e3f4a5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.execute(f'CREATE DOMAIN "{PROTOCOL_SCHEMA}"."application/octet-stream" AS bytea')
  op.execute(f'DROP FUNCTION "{PROTOCOL_SCHEMA}".read_storage_blob(uuid)')
  op.execute(
    f"""
    CREATE FUNCTION "{PROTOCOL_SCHEMA}".read_storage_blob(blob_id uuid)
    RETURNS "{PROTOCOL_SCHEMA}"."application/octet-stream"
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

      RETURN stored_data::"{PROTOCOL_SCHEMA}"."application/octet-stream";
    END
    $$
    """
  )
  op.execute(
    f'REVOKE ALL ON FUNCTION "{PROTOCOL_SCHEMA}".read_storage_blob(uuid) FROM PUBLIC'
  )
  op.execute("NOTIFY pgrst, 'reload schema'")


def downgrade() -> None:
  op.execute(f'DROP FUNCTION "{PROTOCOL_SCHEMA}".read_storage_blob(uuid)')
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
    f'REVOKE ALL ON FUNCTION "{PROTOCOL_SCHEMA}".read_storage_blob(uuid) FROM PUBLIC'
  )
  op.execute(f'DROP DOMAIN "{PROTOCOL_SCHEMA}"."application/octet-stream"')
  op.execute("NOTIFY pgrst, 'reload schema'")
