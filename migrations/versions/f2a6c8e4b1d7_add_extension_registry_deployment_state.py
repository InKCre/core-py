"""Add Extension Registry deployment installation and peer binding state.

Revision ID: f2a6c8e4b1d7
Revises: d9f4e2a1b7c3
Create Date: 2026-08-10
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f2a6c8e4b1d7"
down_revision: str | Sequence[str] | None = "d9f4e2a1b7c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_PROTOCOL_SCHEMA = "inkcre"
_COORDINATE_SEGMENT_PATTERN = r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$"
_SEMVER_PATTERN = (
  r"^(0|[1-9][0-9]*)[.](0|[1-9][0-9]*)[.](0|[1-9][0-9]*)"
  r"(-(0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
  r"([.](0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?$"
)
_TARGET_KEY_PATTERN = r"^[a-z0-9]([a-z0-9._-]{0,126}[a-z0-9])?$"
_TARGET_DIGEST_PATTERN = r"^sha256:[0-9a-f]{64}$"


def upgrade() -> None:
  """Create additive Registry state without reinterpreting legacy extensions."""
  op.create_table(
    "extension_installations",
    sa.Column("namespace", sa.Text(), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("version", sa.Text(), nullable=False),
    sa.Column(
      "config",
      postgresql.JSONB(astext_type=sa.Text()),
      server_default=sa.text("'{}'::jsonb"),
      nullable=False,
    ),
    sa.Column(
      "config_schema",
      postgresql.JSONB(astext_type=sa.Text()),
      server_default=sa.text("'{}'::jsonb"),
      nullable=False,
    ),
    sa.CheckConstraint(
      f"namespace ~ '{_COORDINATE_SEGMENT_PATTERN}'",
      name="extension_installations_namespace_canonical",
    ),
    sa.CheckConstraint(
      f"name ~ '{_COORDINATE_SEGMENT_PATTERN}'",
      name="extension_installations_name_canonical",
    ),
    sa.CheckConstraint(
      f"version ~ '{_SEMVER_PATTERN}'",
      name="extension_installations_version_canonical",
    ),
    sa.PrimaryKeyConstraint("namespace", "name"),
    sa.UniqueConstraint(
      "namespace",
      "name",
      "version",
      name="extension_installations_coordinate_version_key",
    ),
    schema=_PROTOCOL_SCHEMA,
  )

  op.create_table(
    "extension_peer_bindings",
    sa.Column("namespace", sa.Text(), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("version", sa.Text(), nullable=False),
    sa.Column("peer_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("target_key", sa.Text(), nullable=False),
    sa.Column("target_digest", sa.Text(), nullable=False),
    sa.CheckConstraint(
      f"namespace ~ '{_COORDINATE_SEGMENT_PATTERN}'",
      name="extension_peer_bindings_namespace_canonical",
    ),
    sa.CheckConstraint(
      f"name ~ '{_COORDINATE_SEGMENT_PATTERN}'",
      name="extension_peer_bindings_name_canonical",
    ),
    sa.CheckConstraint(
      f"version ~ '{_SEMVER_PATTERN}'",
      name="extension_peer_bindings_version_canonical",
    ),
    sa.CheckConstraint(
      f"target_key ~ '{_TARGET_KEY_PATTERN}'",
      name="extension_peer_bindings_target_key_canonical",
    ),
    sa.CheckConstraint(
      f"target_digest ~ '{_TARGET_DIGEST_PATTERN}'",
      name="extension_peer_bindings_target_digest_canonical",
    ),
    sa.ForeignKeyConstraint(
      ["namespace", "name", "version"],
      [
        f"{_PROTOCOL_SCHEMA}.extension_installations.namespace",
        f"{_PROTOCOL_SCHEMA}.extension_installations.name",
        f"{_PROTOCOL_SCHEMA}.extension_installations.version",
      ],
      name="extension_peer_bindings_installation_fkey",
      ondelete="RESTRICT",
      deferrable=True,
      initially="DEFERRED",
    ),
    sa.ForeignKeyConstraint(
      ["peer_id"],
      [f"{_PROTOCOL_SCHEMA}.clients.id"],
      name="extension_peer_bindings_peer_fkey",
      ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint("namespace", "name", "peer_id"),
    schema=_PROTOCOL_SCHEMA,
  )


def downgrade() -> None:
  """Remove only the additive Registry deployment state."""
  op.drop_table("extension_peer_bindings", schema=_PROTOCOL_SCHEMA)
  op.drop_table("extension_installations", schema=_PROTOCOL_SCHEMA)
