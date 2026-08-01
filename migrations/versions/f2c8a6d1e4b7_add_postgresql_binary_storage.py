"""add PostgreSQL binary storage

Revision ID: f2c8a6d1e4b7
Revises: d9f4e2a1b7c3
Create Date: 2026-08-01

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.database_contract import PROTOCOL_SCHEMA


revision: str = "f2c8a6d1e4b7"
down_revision: str | Sequence[str] | None = "d9f4e2a1b7c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.create_table(
    "storage_blobs",
    sa.Column(
      "id",
      sa.UUID(),
      server_default=sa.text("gen_random_uuid()"),
      nullable=False,
    ),
    sa.Column("data", sa.LargeBinary(), nullable=False),
    sa.PrimaryKeyConstraint("id"),
    schema=PROTOCOL_SCHEMA,
  )


def downgrade() -> None:
  op.drop_table("storage_blobs", schema=PROTOCOL_SCHEMA)
