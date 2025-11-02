"""add github extension

Revision ID: c5_add_github_extension
Revises: b6c0f730d897
Create Date: 2025-11-02 05:16:58.971179

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5_add_github_extension'
down_revision: Union[str, Sequence[str], None] = 'b6c0f730d897'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        INSERT INTO extensions (id, version, disabled, config, state)
        VALUES ('github', '0.1.0', false, '{}', '{}')
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        """
        DELETE FROM extensions WHERE id = 'github'
        """
    )
