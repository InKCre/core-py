"""Add deployment-wide Extension setup state.

Revision ID: c6d7e8f9a0b1
Revises: 3f7a9c2d5e1b
Create Date: 2026-08-16
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.database_contract.constants import (
  CONTRACT_REVISION,
  INTERNAL_SCHEMA,
  PROTOCOL_SCHEMA,
)


revision: str = "c6d7e8f9a0b1"
down_revision: str | Sequence[str] | None = "3f7a9c2d5e1b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _replace_state_guard(*, include_setup_state: bool) -> None:
  state_insert_guard = (
    """
      IF TG_OP = 'INSERT' AND NEW.state <> '{}'::jsonb THEN
        RAISE EXCEPTION 'extensions.state must be empty on insert'
          USING ERRCODE = '23514';
      END IF;
  """
    if include_setup_state
    else ""
  )
  state_version_guard = (
    """
      IF TG_OP = 'UPDATE'
        AND OLD.state <> '{}'::jsonb
        AND NEW.version IS DISTINCT FROM OLD.version
      THEN
        RAISE EXCEPTION 'cannot change extension version while state is not empty'
          USING ERRCODE = '23514';
      END IF;
  """
    if include_setup_state
    else ""
  )
  op.execute(
    f"""
    CREATE OR REPLACE FUNCTION {INTERNAL_SCHEMA}.enforce_extension_state_authority()
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


def _set_contract_revision(value: str) -> None:
  op.execute(
    sa.text(
      f"""
      UPDATE {INTERNAL_SCHEMA}.contract_state
      SET contract_revision = :revision,
          updated_at = CURRENT_TIMESTAMP
      WHERE singleton
      """
    ).bindparams(revision=value)
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
    schema=PROTOCOL_SCHEMA,
  )
  op.create_check_constraint(
    "extensions_state_object",
    "extensions",
    "jsonb_typeof(state) = 'object'",
    schema=PROTOCOL_SCHEMA,
  )
  _replace_state_guard(include_setup_state=True)
  _set_contract_revision(CONTRACT_REVISION)


def downgrade() -> None:
  _replace_state_guard(include_setup_state=False)
  op.drop_constraint(
    "extensions_state_object",
    "extensions",
    schema=PROTOCOL_SCHEMA,
    type_="check",
  )
  op.drop_column("extensions", "state", schema=PROTOCOL_SCHEMA)
  _set_contract_revision("extension-registry-feature-retrieval-v1")
