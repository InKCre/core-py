"""add job abort request

Revision ID: d41cc84db0c5
Revises: 143c4f4adc85
Create Date: 2026-09-14 13:16:59.543435

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d41cc84db0c5"
down_revision: str | Sequence[str] | None = "143c4f4adc85"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  """Upgrade schema."""
  op.add_column(
    "jobs",
    sa.Column(
      "abort_requested", sa.Boolean(), server_default=sa.text("false"), nullable=False
    ),
    schema="inkcre",
  )


def downgrade() -> None:
  """Downgrade schema."""
  op.drop_column("jobs", "abort_requested", schema="inkcre")
