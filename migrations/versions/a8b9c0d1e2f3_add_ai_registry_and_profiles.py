"""add AI registry, profiles, and profile-scoped embedding records

Revision ID: a8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-08-07

"""

from collections.abc import Sequence

from alembic import op
import pgvector.sqlalchemy
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql

from app.database_contract import INTERNAL_SCHEMA, PROTOCOL_SCHEMA


revision: str = "a8b9c0d1e2f3"
down_revision: str | Sequence[str] | None = "f7a8b9c0d1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_TIMESTAMP_TABLES = (
  "ai_providers",
  "ai_models",
  "embedding_profiles",
  "block_embeddings",
  "relation_embeddings",
)


def _timestamps() -> tuple[sa.Column, sa.Column]:
  return (
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
  )


def _create_timestamp_trigger(table_name: str) -> None:
  op.execute(
    f"""
    CREATE TRIGGER update_{table_name}_updated_at
    BEFORE UPDATE ON "{PROTOCOL_SCHEMA}"."{table_name}"
    FOR EACH ROW EXECUTE FUNCTION "{INTERNAL_SCHEMA}".update_updated_at_column()
    """
  )


def upgrade() -> None:
  # Legacy vectors cannot identify a provider/model/profile and are disposable derived data.
  op.drop_table("relation_embeddings", schema=PROTOCOL_SCHEMA)
  op.drop_table("block_embeddings", schema=PROTOCOL_SCHEMA)

  op.create_table(
    "ai_dialects",
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
    "ai_providers",
    sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("dialect", sa.Text(), nullable=False),
    sa.Column(
      "config",
      sqlalchemy.dialects.postgresql.JSONB(astext_type=sa.Text()),
      server_default=sa.text("'{}'::jsonb"),
      nullable=False,
    ),
    sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
    *_timestamps(),
    sa.ForeignKeyConstraint(
      ["dialect"],
      [f"{PROTOCOL_SCHEMA}.ai_dialects.id"],
      onupdate="CASCADE",
      ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint("id"),
    schema=PROTOCOL_SCHEMA,
  )
  op.create_table(
    "ai_models",
    sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
    sa.Column("provider", sa.BigInteger(), nullable=False),
    sa.Column("native_model_id", sa.Text(), nullable=False),
    sa.Column("name", sa.Text(), nullable=True),
    sa.Column(
      "capabilities",
      sqlalchemy.dialects.postgresql.JSONB(astext_type=sa.Text()),
      nullable=False,
    ),
    sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
    *_timestamps(),
    sa.ForeignKeyConstraint(
      ["provider"],
      [f"{PROTOCOL_SCHEMA}.ai_providers.id"],
      onupdate="CASCADE",
      ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint("id"),
    sa.UniqueConstraint(
      "provider",
      "native_model_id",
      name="uq_ai_models_provider_native_model",
    ),
    schema=PROTOCOL_SCHEMA,
  )
  op.create_table(
    "embedding_profiles",
    sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
    sa.Column("name", sa.Text(), nullable=True),
    sa.Column("ai_model", sa.BigInteger(), nullable=False),
    sa.Column("dimensions", sa.Integer(), nullable=False),
    *_timestamps(),
    sa.CheckConstraint("dimensions > 0", name="ck_embedding_profiles_dimensions_positive"),
    sa.ForeignKeyConstraint(
      ["ai_model"],
      [f"{PROTOCOL_SCHEMA}.ai_models.id"],
      onupdate="CASCADE",
      ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint("id"),
    schema=PROTOCOL_SCHEMA,
  )
  op.create_table(
    "block_embeddings",
    sa.Column("profile", sa.BigInteger(), nullable=False),
    sa.Column("block", sa.Integer(), nullable=False),
    sa.Column("embedding", pgvector.sqlalchemy.VECTOR(), nullable=False),
    *_timestamps(),
    sa.ForeignKeyConstraint(
      ["block"],
      [f"{PROTOCOL_SCHEMA}.blocks.id"],
      onupdate="CASCADE",
      ondelete="CASCADE",
    ),
    sa.ForeignKeyConstraint(
      ["profile"],
      [f"{PROTOCOL_SCHEMA}.embedding_profiles.id"],
      onupdate="CASCADE",
      ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint("profile", "block"),
    schema=PROTOCOL_SCHEMA,
  )
  op.create_table(
    "relation_embeddings",
    sa.Column("profile", sa.BigInteger(), nullable=False),
    sa.Column("relation", sa.Integer(), nullable=False),
    sa.Column("embedding", pgvector.sqlalchemy.VECTOR(), nullable=False),
    *_timestamps(),
    sa.ForeignKeyConstraint(
      ["profile"],
      [f"{PROTOCOL_SCHEMA}.embedding_profiles.id"],
      onupdate="CASCADE",
      ondelete="RESTRICT",
    ),
    sa.ForeignKeyConstraint(
      ["relation"],
      [f"{PROTOCOL_SCHEMA}.relations.id"],
      onupdate="CASCADE",
      ondelete="CASCADE",
    ),
    sa.PrimaryKeyConstraint("profile", "relation"),
    schema=PROTOCOL_SCHEMA,
  )

  for table_name in _TIMESTAMP_TABLES:
    _create_timestamp_trigger(table_name)

  op.execute(
    f"""
    CREATE FUNCTION "{INTERNAL_SCHEMA}".reject_ai_model_identity_update()
    RETURNS trigger
    LANGUAGE plpgsql
    SET search_path = pg_catalog
    AS $$
    BEGIN
      IF NEW.provider IS DISTINCT FROM OLD.provider
         OR NEW.native_model_id IS DISTINCT FROM OLD.native_model_id THEN
        RAISE EXCEPTION 'AI model provider/native_model_id identity is immutable'
          USING ERRCODE = '23514';
      END IF;
      RETURN NEW;
    END
    $$
    """
  )
  op.execute(
    f"""
    CREATE TRIGGER reject_ai_model_identity_update
    BEFORE UPDATE ON "{PROTOCOL_SCHEMA}".ai_models
    FOR EACH ROW EXECUTE FUNCTION "{INTERNAL_SCHEMA}".reject_ai_model_identity_update()
    """
  )
  op.execute("NOTIFY pgrst, 'reload schema'")


def downgrade() -> None:
  op.execute(
    "DROP TRIGGER IF EXISTS reject_ai_model_identity_update "
    f'ON "{PROTOCOL_SCHEMA}".ai_models'
  )
  op.execute(
    f'DROP FUNCTION IF EXISTS "{INTERNAL_SCHEMA}".reject_ai_model_identity_update()'
  )
  for table_name in reversed(_TIMESTAMP_TABLES):
    op.execute(
      f"DROP TRIGGER IF EXISTS update_{table_name}_updated_at "
      f'ON "{PROTOCOL_SCHEMA}"."{table_name}"'
    )

  op.drop_table("relation_embeddings", schema=PROTOCOL_SCHEMA)
  op.drop_table("block_embeddings", schema=PROTOCOL_SCHEMA)
  op.drop_table("embedding_profiles", schema=PROTOCOL_SCHEMA)
  op.drop_table("ai_models", schema=PROTOCOL_SCHEMA)
  op.drop_table("ai_providers", schema=PROTOCOL_SCHEMA)
  op.drop_table("ai_dialects", schema=PROTOCOL_SCHEMA)

  op.create_table(
    "block_embeddings",
    sa.Column("id", sa.Integer(), nullable=False),
    sa.Column("embedding", pgvector.sqlalchemy.VECTOR(dim=1024), nullable=False),
    sa.Column(
      "updated_at",
      sa.TIMESTAMP(timezone=True),
      nullable=True,
    ),
    sa.ForeignKeyConstraint(
      ["id"],
      [f"{PROTOCOL_SCHEMA}.blocks.id"],
      onupdate="CASCADE",
      ondelete="CASCADE",
    ),
    sa.PrimaryKeyConstraint("id"),
    schema=PROTOCOL_SCHEMA,
  )
  op.create_table(
    "relation_embeddings",
    sa.Column("id", sa.Integer(), nullable=False),
    sa.Column("embedding", pgvector.sqlalchemy.VECTOR(dim=1024), nullable=False),
    sa.Column(
      "updated_at",
      sa.TIMESTAMP(timezone=True),
      nullable=True,
    ),
    sa.ForeignKeyConstraint(
      ["id"],
      [f"{PROTOCOL_SCHEMA}.relations.id"],
      onupdate="CASCADE",
      ondelete="CASCADE",
    ),
    sa.PrimaryKeyConstraint("id"),
    schema=PROTOCOL_SCHEMA,
  )
  op.execute("NOTIFY pgrst, 'reload schema'")
