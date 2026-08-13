"""Add deployment-wide Extension state authority.

Revision ID: c7d8e9f0a1b2
Revises: b8c1d2e3f4a5
Create Date: 2026-08-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c7d8e9f0a1b2"
down_revision: str | Sequence[str] | None = "b8c1d2e3f4a5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PROTOCOL_SCHEMA = "inkcre"
_INTERNAL_SCHEMA = "inkcre_internal"


def _replace_state_guard(*, include_extension_state: bool) -> None:
  state_insert_guard = """
      IF TG_OP = 'INSERT' AND NEW.state <> '{}'::jsonb THEN
        RAISE EXCEPTION 'extensions.state must be empty on insert'
          USING ERRCODE = '23514';
      END IF;
  """ if include_extension_state else ""
  state_version_guard = """
      IF TG_OP = 'UPDATE'
        AND OLD.state <> '{}'::jsonb
        AND NEW.version IS DISTINCT FROM OLD.version
      THEN
        RAISE EXCEPTION 'cannot change extension version while state is not empty'
          USING ERRCODE = '23514';
      END IF;
  """ if include_extension_state else ""
  op.execute(
    f"""
    CREATE OR REPLACE FUNCTION {_INTERNAL_SCHEMA}.enforce_extension_state_authority()
    RETURNS trigger
    LANGUAGE plpgsql
    SET search_path = pg_catalog
    AS $$
    BEGIN
      IF TG_OP = 'INSERT' AND cardinality(NEW.enabled) <> 0 THEN
        RAISE EXCEPTION 'extensions.enabled must be empty on insert'
          USING ERRCODE = '23514';
      END IF;
      {state_insert_guard}
      IF TG_OP = 'UPDATE'
        AND cardinality(OLD.enabled) <> 0
        AND NEW.version IS DISTINCT FROM OLD.version
      THEN
        RAISE EXCEPTION 'cannot change extension version while peers are enabled'
          USING ERRCODE = '23514';
      END IF;
      {state_version_guard}
      IF TG_OP = 'DELETE' AND cardinality(OLD.enabled) <> 0 THEN
        RAISE EXCEPTION 'cannot delete extension while peers are enabled'
          USING ERRCODE = '23514';
      END IF;
      IF TG_OP = 'DELETE' THEN
        RETURN OLD;
      END IF;
      RETURN NEW;
    END
    $$
    """
  )


def upgrade() -> None:
  op.add_column(
    "extensions",
    sa.Column(
      "state",
      postgresql.JSONB(astext_type=sa.Text()),
      server_default=sa.text("'{}'::jsonb"),
      nullable=False,
    ),
    schema=_PROTOCOL_SCHEMA,
  )
  op.create_check_constraint(
    "extensions_state_object",
    "extensions",
    "jsonb_typeof(state) = 'object'",
    schema=_PROTOCOL_SCHEMA,
  )
  _replace_state_guard(include_extension_state=True)


def downgrade() -> None:
  _replace_state_guard(include_extension_state=False)
  op.drop_constraint(
    "extensions_state_object",
    "extensions",
    schema=_PROTOCOL_SCHEMA,
    type_="check",
  )
  op.drop_column("extensions", "state", schema=_PROTOCOL_SCHEMA)
