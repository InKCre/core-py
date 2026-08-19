"""add relation endpoint indexes

Revision ID: 50b2c08dd267
Revises: 3f7a9c2d5e1b
Create Date: 2026-08-18 22:17:44.391102

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.database_contract import PROTOCOL_SCHEMA


# revision identifiers, used by Alembic.
revision: str = "50b2c08dd267"
down_revision: str | Sequence[str] | None = "3f7a9c2d5e1b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.create_index(
    "relations_from_id_desc_idx",
    "relations",
    ["from_", sa.literal_column("id DESC")],
    unique=False,
    schema=PROTOCOL_SCHEMA,
  )
  op.create_index(
    "relations_to_id_desc_idx",
    "relations",
    ["to_", sa.literal_column("id DESC")],
    unique=False,
    schema=PROTOCOL_SCHEMA,
  )


def downgrade() -> None:
  op.drop_index(
    "relations_to_id_desc_idx",
    table_name="relations",
    schema=PROTOCOL_SCHEMA,
  )
  op.drop_index(
    "relations_from_id_desc_idx",
    table_name="relations",
    schema=PROTOCOL_SCHEMA,
  )
