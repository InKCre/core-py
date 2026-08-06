"""add reusable Agent definitions

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
Create Date: 2026-08-07

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql

from app.database_contract import INTERNAL_SCHEMA, PROTOCOL_SCHEMA


revision: str = "b9c0d1e2f3a4"
down_revision: str | Sequence[str] | None = "a8b9c0d1e2f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.create_table(
    "agents",
    sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("system_prompt", sa.Text(), nullable=False),
    sa.Column(
      "tools",
      sqlalchemy.dialects.postgresql.ARRAY(sa.Text()),
      server_default=sa.text("'{}'::text[]"),
      nullable=False,
    ),
    sa.Column(
      "tool_choice",
      sqlalchemy.dialects.postgresql.JSONB(astext_type=sa.Text()),
      nullable=True,
    ),
    sa.Column("model", sa.BigInteger(), nullable=False),
    sa.Column("max_model_calls_per_turn", sa.Integer(), nullable=False),
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
    sa.CheckConstraint(
      "max_model_calls_per_turn > 0",
      name="ck_agents_max_model_calls_per_turn_positive",
    ),
    sa.ForeignKeyConstraint(
      ["model"],
      [f"{PROTOCOL_SCHEMA}.ai_models.id"],
      onupdate="CASCADE",
      ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint("id"),
    schema=PROTOCOL_SCHEMA,
  )
  op.execute(
    f"""
    CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON "{PROTOCOL_SCHEMA}".agents
    FOR EACH ROW EXECUTE FUNCTION "{INTERNAL_SCHEMA}".update_updated_at_column()
    """
  )
  op.execute("NOTIFY pgrst, 'reload schema'")


def downgrade() -> None:
  op.execute(
    f'DROP TRIGGER IF EXISTS update_agents_updated_at ON "{PROTOCOL_SCHEMA}".agents'
  )
  op.drop_table("agents", schema=PROTOCOL_SCHEMA)
  op.execute("NOTIFY pgrst, 'reload schema'")
