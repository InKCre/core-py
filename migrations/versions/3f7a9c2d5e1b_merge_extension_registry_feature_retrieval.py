"""Merge native Extension Registry and feature-retrieval histories.

Revision ID: 3f7a9c2d5e1b
Revises: 1e4c7a9b2d5f, b8c1d2e3f4a5
Create Date: 2026-08-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.database_contract.constants import CONTRACT_REVISION, INTERNAL_SCHEMA


revision: str = "3f7a9c2d5e1b"
down_revision: str | Sequence[str] | None = (
  "1e4c7a9b2d5f",
  "b8c1d2e3f4a5",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  """Publish the combined artifact contract after both branches converge."""
  # The Registry branch was created while the shared relation was still named
  # ``clients``. Re-publish its SQL-language body after the feature branch's
  # client-to-peer rename so future invocations resolve the final authority.
  op.execute(
    """
    CREATE OR REPLACE FUNCTION inkcre.set_extension_peer_enabled(
      p_name text,
      p_peer_id uuid,
      p_enabled boolean
    )
    RETURNS SETOF inkcre.extensions
    LANGUAGE sql
    VOLATILE
    STRICT
    SECURITY DEFINER
    SET search_path = pg_catalog, inkcre
    AS $$
      UPDATE inkcre.extensions
      SET enabled = CASE
        WHEN p_enabled AND NOT (p_peer_id = ANY(enabled))
          THEN array_append(enabled, p_peer_id)
        WHEN NOT p_enabled
          THEN array_remove(enabled, p_peer_id)
        ELSE enabled
      END
      WHERE name = p_name
        AND EXISTS (
          SELECT 1
          FROM inkcre.peers
          WHERE id = p_peer_id
        )
      RETURNING *
    $$
    """
  )
  op.execute(
    sa.text(
      f"""
      UPDATE {INTERNAL_SCHEMA}.contract_state
      SET contract_revision = :revision,
          updated_at = CURRENT_TIMESTAMP
      WHERE singleton
      """
    ).bindparams(revision=CONTRACT_REVISION)
  )


def downgrade() -> None:
  """Leave the prior branch-specific revision explicit when the merge is removed."""
  op.execute(
    sa.text(
      f"""
      UPDATE {INTERNAL_SCHEMA}.contract_state
      SET contract_revision = 'lexical-retrieval-runtime-v1',
          updated_at = CURRENT_TIMESTAMP
      WHERE singleton
      """
    )
  )
