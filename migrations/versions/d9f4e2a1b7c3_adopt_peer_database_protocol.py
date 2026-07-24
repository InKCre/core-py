"""Adopt the provider-neutral peer database protocol.

Revision ID: d9f4e2a1b7c3
Revises: c4e8a7b6d5f0
Create Date: 2026-07-24
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.database_contract.constants import (
  CONTRACT_REVISION,
  INTERNAL_SCHEMA,
  JWT_AUDIENCE,
  JWT_ISSUER,
  JWT_MAX_LIFETIME_SECONDS,
  JWT_ROLE,
  PROTOCOL_SCHEMA,
)


revision: str = "d9f4e2a1b7c3"
down_revision: str | Sequence[str] | None = "c4e8a7b6d5f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_APPLICATION_TABLES = (
  "block_embeddings",
  "blocks",
  "clients",
  "extensions",
  "logs",
  "relation_embeddings",
  "relations",
  "sources",
  "sources_collect_jobs",
  "sources_types",
  "storage_types",
  "storages",
)


def _move_relation(table_name: str) -> None:
  op.execute(
    f"""
    DO $$
    BEGIN
      IF to_regclass('public.{table_name}') IS NOT NULL
         AND to_regclass('{PROTOCOL_SCHEMA}.{table_name}') IS NOT NULL THEN
        RAISE EXCEPTION
          'both public.{table_name} and {PROTOCOL_SCHEMA}.{table_name} exist';
      ELSIF to_regclass('public.{table_name}') IS NOT NULL THEN
        ALTER TABLE public."{table_name}" SET SCHEMA "{PROTOCOL_SCHEMA}";
      ELSIF to_regclass('{PROTOCOL_SCHEMA}.{table_name}') IS NULL THEN
        RAISE EXCEPTION 'required application table is missing: {table_name}';
      END IF;
    END
    $$;
    """
  )


def upgrade() -> None:
  """Move the admitted protocol into dedicated, provider-neutral schemas."""
  op.execute(f'CREATE SCHEMA IF NOT EXISTS "{PROTOCOL_SCHEMA}"')
  op.execute(f'CREATE SCHEMA IF NOT EXISTS "{INTERNAL_SCHEMA}"')

  for table_name in _APPLICATION_TABLES:
    _move_relation(table_name)

  op.execute(
    f"""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1
        FROM pg_type AS type
        JOIN pg_namespace AS namespace ON namespace.oid = type.typnamespace
        WHERE namespace.nspname = 'public'
          AND type.typname = 'sourcecollectjobstatus'
      ) AND NOT EXISTS (
        SELECT 1
        FROM pg_type AS type
        JOIN pg_namespace AS namespace ON namespace.oid = type.typnamespace
        WHERE namespace.nspname = '{PROTOCOL_SCHEMA}'
          AND type.typname = 'sourcecollectjobstatus'
      ) THEN
        ALTER TYPE public.sourcecollectjobstatus SET SCHEMA "{PROTOCOL_SCHEMA}";
      END IF;
    END
    $$;
    """
  )

  op.execute(
    f"""
    DO $$
    BEGIN
      IF to_regprocedure('public.update_updated_at_column()') IS NOT NULL
         AND to_regprocedure(
           '{PROTOCOL_SCHEMA}.update_updated_at_column()'
         ) IS NULL THEN
        ALTER FUNCTION public.update_updated_at_column()
          SET SCHEMA "{PROTOCOL_SCHEMA}";
      END IF;
    END
    $$;
    """
  )

  op.create_table(
    "contract_state",
    sa.Column("singleton", sa.Boolean(), nullable=False),
    sa.Column("contract_revision", sa.Text(), nullable=False),
    sa.Column("environment", sa.Text(), nullable=False),
    sa.Column("owner_role", sa.Text(), nullable=False),
    sa.Column(
      "updated_at",
      sa.TIMESTAMP(timezone=True),
      server_default=sa.text("CURRENT_TIMESTAMP"),
      nullable=False,
    ),
    sa.CheckConstraint("singleton", name="contract_state_singleton_true"),
    sa.CheckConstraint(
      "environment IN ('runtime', 'development', 'preview', 'production')",
      name="contract_state_environment_valid",
    ),
    sa.PrimaryKeyConstraint("singleton"),
    schema=INTERNAL_SCHEMA,
  )
  op.execute(
    sa.text(
      f"""
      INSERT INTO "{INTERNAL_SCHEMA}".contract_state (
        singleton,
        contract_revision,
        environment,
        owner_role
      )
      VALUES (TRUE, :revision, 'runtime', current_user)
      """
    ).bindparams(revision=CONTRACT_REVISION)
  )

  op.execute(
    f"""
    CREATE OR REPLACE FUNCTION "{INTERNAL_SCHEMA}".check_jwt()
    RETURNS void
    LANGUAGE plpgsql
    SECURITY INVOKER
    SET search_path = pg_catalog
    AS $$
    DECLARE
      claims jsonb;
      issued_at numeric;
      expires_at numeric;
      current_epoch numeric := extract(epoch FROM statement_timestamp());
    BEGIN
      claims := nullif(current_setting('request.jwt.claims', true), '')::jsonb;

      IF claims IS NULL
         OR jsonb_typeof(claims -> 'role') <> 'string'
         OR claims ->> 'role' <> '{JWT_ROLE}'
         OR jsonb_typeof(claims -> 'iss') <> 'string'
         OR claims ->> 'iss' <> '{JWT_ISSUER}'
         OR jsonb_typeof(claims -> 'aud') <> 'string'
         OR claims ->> 'aud' <> '{JWT_AUDIENCE}'
         OR jsonb_typeof(claims -> 'iat') <> 'number'
         OR jsonb_typeof(claims -> 'exp') <> 'number'
      THEN
        RAISE insufficient_privilege USING MESSAGE = 'invalid jwt claims';
      END IF;

      issued_at := (claims ->> 'iat')::numeric;
      expires_at := (claims ->> 'exp')::numeric;

      IF issued_at > current_epoch + 60
         OR expires_at <= current_epoch
         OR expires_at <= issued_at
         OR expires_at - issued_at > {JWT_MAX_LIFETIME_SECONDS}
      THEN
        RAISE insufficient_privilege USING MESSAGE = 'invalid jwt lifetime';
      END IF;
    END
    $$;
    """
  )


def downgrade() -> None:
  """Return protocol relations to public without touching cluster roles."""
  op.execute(f'DROP FUNCTION IF EXISTS "{INTERNAL_SCHEMA}".check_jwt()')
  op.drop_table("contract_state", schema=INTERNAL_SCHEMA)

  op.execute(
    f"""
    DO $$
    BEGIN
      IF to_regprocedure(
        '{PROTOCOL_SCHEMA}.update_updated_at_column()'
      ) IS NOT NULL
         AND to_regprocedure('public.update_updated_at_column()') IS NULL THEN
        ALTER FUNCTION "{PROTOCOL_SCHEMA}".update_updated_at_column()
          SET SCHEMA public;
      END IF;
    END
    $$;
    """
  )

  op.execute(
    f"""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1
        FROM pg_type AS type
        JOIN pg_namespace AS namespace ON namespace.oid = type.typnamespace
        WHERE namespace.nspname = '{PROTOCOL_SCHEMA}'
          AND type.typname = 'sourcecollectjobstatus'
      ) AND NOT EXISTS (
        SELECT 1
        FROM pg_type AS type
        JOIN pg_namespace AS namespace ON namespace.oid = type.typnamespace
        WHERE namespace.nspname = 'public'
          AND type.typname = 'sourcecollectjobstatus'
      ) THEN
        ALTER TYPE "{PROTOCOL_SCHEMA}".sourcecollectjobstatus SET SCHEMA public;
      END IF;
    END
    $$;
    """
  )

  for table_name in reversed(_APPLICATION_TABLES):
    op.execute(
      f"""
      DO $$
      BEGIN
        IF to_regclass('{PROTOCOL_SCHEMA}.{table_name}') IS NOT NULL THEN
          ALTER TABLE "{PROTOCOL_SCHEMA}"."{table_name}" SET SCHEMA public;
        END IF;
      END
      $$;
      """
    )

  op.execute(f'DROP SCHEMA IF EXISTS "{INTERNAL_SCHEMA}"')
  op.execute(f'DROP SCHEMA IF EXISTS "{PROTOCOL_SCHEMA}"')
