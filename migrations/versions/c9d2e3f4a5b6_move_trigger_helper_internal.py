"""move trigger helper to the internal schema

Revision ID: c9d2e3f4a5b6
Revises: b8f1c2d3e4a5
Create Date: 2026-08-02

"""

from collections.abc import Sequence

from alembic import op

from app.database_contract import INTERNAL_SCHEMA, PROTOCOL_SCHEMA


revision: str = "c9d2e3f4a5b6"
down_revision: str | Sequence[str] | None = "b8f1c2d3e4a5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.execute(
    f'ALTER FUNCTION "{PROTOCOL_SCHEMA}".update_updated_at_column() '
    f'SET SCHEMA "{INTERNAL_SCHEMA}"'
  )
  op.execute("NOTIFY pgrst, 'reload schema'")


def downgrade() -> None:
  op.execute(
    f'ALTER FUNCTION "{INTERNAL_SCHEMA}".update_updated_at_column() '
    f'SET SCHEMA "{PROTOCOL_SCHEMA}"'
  )
  op.execute("NOTIFY pgrst, 'reload schema'")
