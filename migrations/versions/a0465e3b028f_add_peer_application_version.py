"""add peer application version

Revision ID: a0465e3b028f
Revises: d41cc84db0c5
Create Date: 2026-09-22 20:24:20.666591

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.database_contract import INTERNAL_SCHEMA, PROTOCOL_SCHEMA


revision: str = "a0465e3b028f"
down_revision: str | Sequence[str] | None = "d41cc84db0c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CONTRACT_REVISION = "peer-runtime-identity-v1"
_PREVIOUS_CONTRACT_REVISION = "peer-extension-setup-v1"


def _set_contract_revision(value: str) -> None:
  op.execute(
    sa.text(
      f"""
      UPDATE "{INTERNAL_SCHEMA}".contract_state
      SET contract_revision = :revision,
          updated_at = statement_timestamp()
      WHERE singleton
      """
    ).bindparams(revision=value)
  )


def upgrade() -> None:
  op.add_column(
    "peers",
    sa.Column("application_version", sa.Text(), nullable=True),
    schema=PROTOCOL_SCHEMA,
  )
  _set_contract_revision(_CONTRACT_REVISION)
  op.execute("NOTIFY pgrst, 'reload schema'")


def downgrade() -> None:
  _set_contract_revision(_PREVIOUS_CONTRACT_REVISION)
  op.drop_column("peers", "application_version", schema=PROTOCOL_SCHEMA)
  op.execute("NOTIFY pgrst, 'reload schema'")
