"""add Block lexical retrieval records

Revision ID: 1e4c7a9b2d5f
Revises: 77cd53ad8080
Create Date: 2026-08-13 15:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql

from app.database_contract import PROTOCOL_SCHEMA


revision: str = "1e4c7a9b2d5f"
down_revision: str | Sequence[str] | None = "77cd53ad8080"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
  op.create_table(
    "block_lexical_records",
    sa.Column("block", sa.Integer(), nullable=False),
    sa.Column("label", sa.Text(), nullable=False),
    sa.Column("text", sa.Text(), nullable=True),
    sa.Column(
      "search_vector",
      sqlalchemy.dialects.postgresql.TSVECTOR(),
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
    sa.ForeignKeyConstraint(
      ["block"],
      [f"{PROTOCOL_SCHEMA}.blocks.id"],
      onupdate="CASCADE",
      ondelete="CASCADE",
    ),
    sa.PrimaryKeyConstraint("block"),
    schema=PROTOCOL_SCHEMA,
  )
  op.create_index(
    "block_lexical_records_search_vector_idx",
    "block_lexical_records",
    ["search_vector"],
    unique=False,
    schema=PROTOCOL_SCHEMA,
    postgresql_using="gin",
  )
  op.create_index(
    "block_lexical_records_label_trgm_idx",
    "block_lexical_records",
    ["label"],
    unique=False,
    schema=PROTOCOL_SCHEMA,
    postgresql_using="gin",
    postgresql_ops={"label": "gin_trgm_ops"},
  )
  op.create_index(
    "block_lexical_records_text_trgm_idx",
    "block_lexical_records",
    ["text"],
    unique=False,
    schema=PROTOCOL_SCHEMA,
    postgresql_using="gin",
    postgresql_ops={"text": "gin_trgm_ops"},
  )


def downgrade() -> None:
  op.drop_index(
    "block_lexical_records_text_trgm_idx",
    table_name="block_lexical_records",
    schema=PROTOCOL_SCHEMA,
    postgresql_using="gin",
  )
  op.drop_index(
    "block_lexical_records_label_trgm_idx",
    table_name="block_lexical_records",
    schema=PROTOCOL_SCHEMA,
    postgresql_using="gin",
  )
  op.drop_index(
    "block_lexical_records_search_vector_idx",
    table_name="block_lexical_records",
    schema=PROTOCOL_SCHEMA,
    postgresql_using="gin",
  )
  op.drop_table("block_lexical_records", schema=PROTOCOL_SCHEMA)
