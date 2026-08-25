"""Merge Extension setup and current main migration histories.

Revision ID: d4e6f8a0b2c3
Revises: 50b2c08dd267, c6d7e8f9a0b1
Create Date: 2026-08-24
"""

from collections.abc import Sequence


revision: str = "d4e6f8a0b2c3"
down_revision: str | Sequence[str] | None = (
  "50b2c08dd267",
  "c6d7e8f9a0b1",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  """Converge the two already-complete histories without another data operation."""


def downgrade() -> None:
  """Remove only the merge marker while retaining both parent revisions."""
