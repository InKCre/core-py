"""add_clients_modify_extensions_enabled

Revision ID: a1b2c3d4e5f6
Revises: e5a01f9e69ef
Create Date: 2025-12-31

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "e5a01f9e69ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  """Upgrade schema."""
  # 1. Create clients table
  op.create_table(
    "clients",
    sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column(
      "labels",
      postgresql.ARRAY(sa.Text()),
      server_default=sa.text("'{}'::text[]"),
      nullable=True,
    ),
    sa.Column("rest_api_url", sa.Text(), nullable=True, server_default=None),
    sa.Column(
      "created_at",
      sa.TIMESTAMP(timezone=True),
      server_default=sa.text("CURRENT_TIMESTAMP"),
      nullable=True,
    ),
    sa.PrimaryKeyConstraint("id"),
  )

  # 2. Add enabled column to extensions (UUID array)
  op.add_column(
    "extensions",
    sa.Column(
      "enabled",
      postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
      server_default=sa.text("'{}'::uuid[]"),
      nullable=False,
    ),
  )

  # 3. Migrate data: disabled=false -> keep empty (will need manual re-enable)
  # Extensions that were disabled=true are now enabled=[] (same semantic)
  # Extensions that were disabled=false will also become enabled=[]
  # (breaking change - requires manual re-enable after migration)

  # 4. Drop disabled column
  op.drop_column("extensions", "disabled")

  # 5. Grant permissions on clients table
  op.execute("GRANT ALL ON public.clients TO authenticated;")


def downgrade() -> None:
  """Downgrade schema."""
  # 1. Add back disabled column
  op.add_column(
    "extensions",
    sa.Column("disabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
  )

  # 2. Migrate data: empty enabled array -> disabled=true
  op.execute("""
        UPDATE extensions
        SET disabled = (CASE WHEN array_length(enabled, 1) IS NULL OR array_length(enabled, 1) = 0
                        THEN true ELSE false END)
    """)

  # 3. Drop enabled column
  op.drop_column("extensions", "enabled")

  # 4. Drop clients table
  op.drop_table("clients")
