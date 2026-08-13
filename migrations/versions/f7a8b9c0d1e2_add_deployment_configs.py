"""add deployment configs and database-owned row timestamps

Revision ID: f7a8b9c0d1e2
Revises: e1f4a5b6c7d8
Create Date: 2026-08-07

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql

from app.database_contract import INTERNAL_SCHEMA, PROTOCOL_SCHEMA


revision: str = "f7a8b9c0d1e2"
down_revision: str | Sequence[str] | None = "e1f4a5b6c7d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.create_table(
    "configs",
    sa.Column("key", sa.Text(), nullable=False),
    sa.Column("schema", sa.Text(), nullable=False),
    sa.Column(
      "value",
      sqlalchemy.dialects.postgresql.JSONB(astext_type=sa.Text()),
      nullable=False,
    ),
    sa.Column(
      "created_at",
      sa.TIMESTAMP(timezone=True),
      server_default=sa.text("CURRENT_TIMESTAMP"),
      nullable=False,
    ),
    sa.Column(
      "updated_at",
      sa.TIMESTAMP(timezone=True),
      server_default=sa.text("CURRENT_TIMESTAMP"),
      nullable=False,
    ),
    sa.PrimaryKeyConstraint("key"),
    schema=PROTOCOL_SCHEMA,
  )

  op.execute(
    f"""
    CREATE OR REPLACE FUNCTION "{INTERNAL_SCHEMA}".update_updated_at_column()
    RETURNS trigger
    LANGUAGE plpgsql
    SET search_path = pg_catalog
    AS $$
    BEGIN
      IF NEW IS DISTINCT FROM OLD THEN
        NEW.updated_at = statement_timestamp();
      END IF;
      RETURN NEW;
    END
    $$
    """
  )
  op.execute(
    f"""
    CREATE TRIGGER update_relations_updated_at
    BEFORE UPDATE ON "{PROTOCOL_SCHEMA}".relations
    FOR EACH ROW EXECUTE FUNCTION "{INTERNAL_SCHEMA}".update_updated_at_column()
    """
  )
  op.execute(
    f"""
    CREATE TRIGGER update_configs_updated_at
    BEFORE UPDATE ON "{PROTOCOL_SCHEMA}".configs
    FOR EACH ROW EXECUTE FUNCTION "{INTERNAL_SCHEMA}".update_updated_at_column()
    """
  )
  op.execute("NOTIFY pgrst, 'reload schema'")


def downgrade() -> None:
  op.execute(
    f'DROP TRIGGER IF EXISTS update_configs_updated_at ON "{PROTOCOL_SCHEMA}".configs'
  )
  op.execute(
    f'DROP TRIGGER IF EXISTS update_relations_updated_at ON "{PROTOCOL_SCHEMA}".relations'
  )
  op.drop_table("configs", schema=PROTOCOL_SCHEMA)
  op.execute(
    f"""
    CREATE OR REPLACE FUNCTION "{INTERNAL_SCHEMA}".update_updated_at_column()
    RETURNS trigger
    LANGUAGE plpgsql
    SET search_path = pg_catalog
    AS $$
    BEGIN
      IF NEW.content <> OLD.content THEN
        NEW.updated_at = CURRENT_TIMESTAMP;
      END IF;
      RETURN NEW;
    END
    $$
    """
  )
  op.execute("NOTIFY pgrst, 'reload schema'")
