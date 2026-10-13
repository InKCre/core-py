"""Separate shared Extensions from per-Peer native selections.

Revision ID: e6a1b2c3d4f5
Revises: 3d9593b0c855
Create Date: 2026-10-13
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


revision: str = "e6a1b2c3d4f5"
down_revision: str | Sequence[str] | None = "3d9593b0c855"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NAME_PATTERN = (
  r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?/"
  r"[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$"
)
_SEMVER_PATTERN = (
  r"^(0|[1-9][0-9]*)[.](0|[1-9][0-9]*)[.](0|[1-9][0-9]*)"
  r"(-(0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
  r"([.](0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?$"
)


def _replace_state_guard() -> None:
  op.execute(
    f"""
    CREATE OR REPLACE FUNCTION {INTERNAL_SCHEMA}.enforce_extension_state_authority()
    RETURNS trigger
    LANGUAGE plpgsql
    SET search_path = pg_catalog
    AS $$
    BEGIN
      IF TG_OP = 'INSERT' AND NEW.state <> '{{}}'::jsonb THEN
        RAISE EXCEPTION 'extensions.state must be empty on insert'
          USING ERRCODE = '23514';
      END IF;
      IF TG_OP = 'DELETE' AND OLD.state <> '{{}}'::jsonb THEN
        RAISE EXCEPTION 'cannot delete Extension while state is not empty'
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
  """Retain legacy state, then make each Peer selection explicit."""
  op.create_table(
    "extension_legacy_snapshots",
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("version", sa.Text(), nullable=False),
    sa.Column(
      "enabled",
      postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
      nullable=False,
    ),
    sa.Column("config_schema", postgresql.JSONB(astext_type=sa.Text())),
    sa.Column(
      "captured_at",
      sa.TIMESTAMP(timezone=True),
      server_default=sa.text("CURRENT_TIMESTAMP"),
      nullable=False,
    ),
    sa.PrimaryKeyConstraint("name"),
    schema=INTERNAL_SCHEMA,
  )
  op.execute(
    f"""
    INSERT INTO {INTERNAL_SCHEMA}.extension_legacy_snapshots
      (name, version, enabled, config_schema)
    SELECT name, version, enabled, config_schema
    FROM {PROTOCOL_SCHEMA}.extensions
    """
  )
  op.create_table(
    "extension_peer_participations",
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("peer_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("distribution", sa.Text(), nullable=True),
    sa.Column("version", sa.Text(), nullable=False),
    sa.Column("enabled", sa.Boolean(), server_default=sa.false(), nullable=False),
    sa.Column("config_schema", postgresql.JSONB(astext_type=sa.Text())),
    sa.CheckConstraint(
      f"name ~ '{_NAME_PATTERN}'",
      name="extension_peer_participations_name_canonical",
    ),
    sa.CheckConstraint(
      f"version ~ '{_SEMVER_PATTERN}'",
      name="extension_peer_participations_version_canonical",
    ),
    sa.CheckConstraint(
      "distribution IS NULL OR distribution IN ('python', 'module_federation')",
      name="extension_peer_participations_distribution_valid",
    ),
    sa.CheckConstraint(
      "config_schema IS NULL OR jsonb_typeof(config_schema) = 'object'",
      name="extension_peer_participations_config_schema_object",
    ),
    sa.CheckConstraint(
      "distribution IS NOT NULL OR config_schema IS NULL",
      name="extension_peer_participations_unresolved_schema_null",
    ),
    sa.ForeignKeyConstraint(
      ["name"], [f"{PROTOCOL_SCHEMA}.extensions.name"], ondelete="CASCADE"
    ),
    sa.ForeignKeyConstraint(
      ["peer_id"], [f"{PROTOCOL_SCHEMA}.peers.id"], ondelete="CASCADE"
    ),
    sa.PrimaryKeyConstraint(
      "name", "peer_id", name="extension_peer_participations_pkey"
    ),
    schema=PROTOCOL_SCHEMA,
  )
  op.execute(
    f"""
    INSERT INTO {PROTOCOL_SCHEMA}.extension_peer_participations
      (name, peer_id, distribution, version, enabled, config_schema)
    SELECT extension.name, peer_id, NULL, extension.version, true, NULL
    FROM {PROTOCOL_SCHEMA}.extensions AS extension
    CROSS JOIN LATERAL unnest(extension.enabled) AS peer_id
    """
  )
  op.execute(
    f"DROP FUNCTION {PROTOCOL_SCHEMA}.set_extension_peer_enabled(text, uuid, boolean)"
  )
  op.execute(
    f"DROP TRIGGER extensions_state_authority ON {PROTOCOL_SCHEMA}.extensions"
  )
  op.execute(
    f"DROP FUNCTION {INTERNAL_SCHEMA}.enforce_extension_state_authority()"
  )
  op.drop_column("extensions", "version", schema=PROTOCOL_SCHEMA)
  op.drop_column("extensions", "enabled", schema=PROTOCOL_SCHEMA)
  op.drop_column("extensions", "config_schema", schema=PROTOCOL_SCHEMA)
  _replace_state_guard()
  _set_contract_revision(CONTRACT_REVISION)
  op.execute("NOTIFY pgrst, 'reload schema'")


def downgrade() -> None:
  """Restore legacy columns only while all selections still match the snapshot."""
  op.execute(
    f"""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1
        FROM {PROTOCOL_SCHEMA}.extension_peer_participations AS participation
        LEFT JOIN {INTERNAL_SCHEMA}.extension_legacy_snapshots AS snapshot
          ON snapshot.name = participation.name
        WHERE snapshot.name IS NULL
           OR participation.distribution IS NOT NULL
           OR participation.version <> snapshot.version
           OR NOT participation.enabled
           OR NOT (participation.peer_id = ANY(snapshot.enabled))
      ) OR EXISTS (
        SELECT 1
        FROM {INTERNAL_SCHEMA}.extension_legacy_snapshots AS snapshot
        CROSS JOIN LATERAL unnest(snapshot.enabled) AS peer_id
        LEFT JOIN {PROTOCOL_SCHEMA}.extension_peer_participations AS participation
          ON participation.name = snapshot.name AND participation.peer_id = peer_id
        WHERE participation.name IS NULL
      ) OR EXISTS (
        SELECT 1
        FROM {PROTOCOL_SCHEMA}.extensions AS extension
        LEFT JOIN {INTERNAL_SCHEMA}.extension_legacy_snapshots AS snapshot
          ON snapshot.name = extension.name
        WHERE snapshot.name IS NULL
      ) THEN
        RAISE EXCEPTION
          'cannot downgrade Extension Peer selections after v2 state has changed';
      END IF;
    END
    $$
    """
  )
  op.execute(
    f"DROP TRIGGER extensions_state_authority ON {PROTOCOL_SCHEMA}.extensions"
  )
  op.execute(
    f"DROP FUNCTION {INTERNAL_SCHEMA}.enforce_extension_state_authority()"
  )
  op.add_column(
    "extensions",
    sa.Column("version", sa.Text(), nullable=True),
    schema=PROTOCOL_SCHEMA,
  )
  op.add_column(
    "extensions",
    sa.Column(
      "enabled",
      postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
      nullable=False,
      server_default=sa.text("'{}'::uuid[]"),
    ),
    schema=PROTOCOL_SCHEMA,
  )
  op.add_column(
    "extensions",
    sa.Column("config_schema", postgresql.JSONB(astext_type=sa.Text())),
    schema=PROTOCOL_SCHEMA,
  )
  op.execute(
    f"""
    UPDATE {PROTOCOL_SCHEMA}.extensions AS extension
    SET version = snapshot.version,
        enabled = snapshot.enabled,
        config_schema = snapshot.config_schema
    FROM {INTERNAL_SCHEMA}.extension_legacy_snapshots AS snapshot
    WHERE snapshot.name = extension.name
    """
  )
  op.alter_column(
    "extensions", "version", nullable=False, schema=PROTOCOL_SCHEMA
  )
  op.create_check_constraint(
    "extensions_version_canonical",
    "extensions",
    f"version ~ '{_SEMVER_PATTERN}'",
    schema=PROTOCOL_SCHEMA,
  )
  op.drop_table("extension_peer_participations", schema=PROTOCOL_SCHEMA)
  op.drop_table("extension_legacy_snapshots", schema=INTERNAL_SCHEMA)
  _set_contract_revision("peer-runtime-identity-v1")
  op.execute("NOTIFY pgrst, 'reload schema'")
