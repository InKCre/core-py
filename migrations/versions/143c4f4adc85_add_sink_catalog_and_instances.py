"""add sink catalog and instances

Revision ID: 143c4f4adc85
Revises: d4e6f8a0b2c3
Create Date: 2026-08-30 14:13:14.923437

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql

from app.database_contract import PROTOCOL_SCHEMA


# revision identifiers, used by Alembic.
revision: str = "143c4f4adc85"
down_revision: str | Sequence[str] | None = "d4e6f8a0b2c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.create_table(
    "sink_types",
    sa.Column("id", sa.Text(), nullable=False),
    sa.Column("description", sa.Text(), nullable=False),
    sa.Column(
      "config_schema",
      sqlalchemy.dialects.postgresql.JSONB(astext_type=sa.Text()),
      server_default=sa.text("'{}'::jsonb"),
      nullable=False,
    ),
    sa.PrimaryKeyConstraint("id"),
    schema=PROTOCOL_SCHEMA,
  )
  op.create_table(
    "sinks",
    sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
    sa.Column("type", sa.Text(), nullable=False),
    sa.Column("nickname", sa.Text(), nullable=True),
    sa.Column(
      "config",
      sqlalchemy.dialects.postgresql.JSONB(astext_type=sa.Text()),
      server_default=sa.text("'{}'::jsonb"),
      nullable=False,
    ),
    sa.Column(
      "enabled",
      sqlalchemy.dialects.postgresql.ARRAY(
        sqlalchemy.dialects.postgresql.UUID(as_uuid=True)
      ),
      server_default=sa.text("'{}'::uuid[]"),
      nullable=False,
    ),
    sa.ForeignKeyConstraint(
      ["type"],
      [f"{PROTOCOL_SCHEMA}.sink_types.id"],
      onupdate="CASCADE",
      ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint("id"),
    schema=PROTOCOL_SCHEMA,
  )


def downgrade() -> None:
  op.drop_table("sinks", schema=PROTOCOL_SCHEMA)
  op.drop_table("sink_types", schema=PROTOCOL_SCHEMA)
