"""Converge rewritten and production schema lineages.

Revision ID: c4e8a7b6d5f0
Revises: a1b2c3d4e5f6
Create Date: 2026-07-23

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c4e8a7b6d5f0"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_REQUIRED_COLUMNS: tuple[tuple[str, str, sa.types.TypeEngine], ...] = (
  ("clients", "config", postgresql.JSONB()),
  ("clients", "config_schema", postgresql.JSONB()),
  ("logs", "timestamp", sa.TIMESTAMP(timezone=True)),
  ("sources", "config", postgresql.JSONB()),
  ("sources", "state", postgresql.JSONB()),
  (
    "sources_collect_jobs",
    "status",
    postgresql.ENUM(
      "pending",
      "running",
      "finished",
      "failed",
      name="sourcecollectjobstatus",
      create_type=False,
    ),
  ),
  ("sources_types", "config_schema", postgresql.JSONB()),
  ("storage_types", "description", sa.Text()),
  ("storage_types", "config_schema", postgresql.JSONB()),
  ("storages", "type", sa.Text()),
  ("storages", "config", postgresql.JSONB()),
)


def _set_required_columns(*, nullable: bool) -> None:
  for table_name, column_name, column_type in _REQUIRED_COLUMNS:
    op.alter_column(
      table_name,
      column_name,
      existing_type=column_type,
      nullable=nullable,
    )


def upgrade() -> None:
  """Converge both known a1b2c3d4e5f6 schema shapes."""
  _set_required_columns(nullable=False)

  op.alter_column(
    "extensions",
    "id",
    existing_type=sa.String(),
    type_=sa.Text(),
    existing_nullable=False,
  )
  op.alter_column(
    "extensions",
    "nickname",
    existing_type=sa.String(),
    type_=sa.Text(),
    existing_nullable=True,
  )
  op.alter_column(
    "sources",
    "nickname",
    existing_type=sa.String(),
    type_=sa.Text(),
    existing_nullable=True,
  )

  op.alter_column(
    "logs",
    "id",
    existing_type=sa.Integer(),
    type_=sa.BigInteger(),
    existing_nullable=False,
  )
  op.execute("ALTER SEQUENCE IF EXISTS public.logs_id_seq AS BIGINT")

  op.drop_constraint("blocks_storage_fkey", "blocks", type_="foreignkey")
  op.create_foreign_key(
    "blocks_storage_fkey",
    "blocks",
    "storages",
    ["storage"],
    ["id"],
    onupdate="CASCADE",
    ondelete="SET NULL",
  )


def downgrade() -> None:
  """Return to the canonical fresh a1b2c3d4e5f6 schema."""
  op.execute(
    """
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1
        FROM public.logs
        WHERE id < -2147483648 OR id > 2147483647
      ) THEN
        RAISE EXCEPTION
          'cannot downgrade logs.id: value exceeds INTEGER range';
      END IF;

      IF EXISTS (
        SELECT 1
        FROM pg_sequences
        WHERE schemaname = 'public'
          AND sequencename = 'logs_id_seq'
          AND last_value > 2147483647
      ) THEN
        RAISE EXCEPTION
          'cannot downgrade logs_id_seq: value exceeds INTEGER range';
      END IF;
    END
    $$;
    """
  )
  op.alter_column(
    "logs",
    "id",
    existing_type=sa.BigInteger(),
    type_=sa.Integer(),
    existing_nullable=False,
  )
  op.execute("ALTER SEQUENCE IF EXISTS public.logs_id_seq AS INTEGER")

  _set_required_columns(nullable=True)
