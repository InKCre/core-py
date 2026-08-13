"""Hard-cut Extension state to one native-Distribution relation.

Revision ID: b8c1d2e3f4a5
Revises: f2a6c8e4b1d7
Create Date: 2026-08-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b8c1d2e3f4a5"
down_revision: str | Sequence[str] | None = "f2a6c8e4b1d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_PROTOCOL_SCHEMA = "inkcre"
_INTERNAL_SCHEMA = "inkcre_internal"
_NAME_PATTERN = (
  r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?/"
  r"[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$"
)
_SEMVER_PATTERN = (
  r"^(0|[1-9][0-9]*)[.](0|[1-9][0-9]*)[.](0|[1-9][0-9]*)"
  r"(-(0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
  r"([.](0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?$"
)


def _create_canonical_extensions() -> None:
  op.create_table(
    "extensions",
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("version", sa.Text(), nullable=False),
    sa.Column(
      "enabled",
      postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
      server_default=sa.text("'{}'::uuid[]"),
      nullable=False,
    ),
    sa.Column("nickname", sa.Text(), nullable=True),
    sa.Column(
      "config",
      postgresql.JSONB(astext_type=sa.Text()),
      server_default=sa.text("'{}'::jsonb"),
      nullable=False,
    ),
    sa.Column(
      "config_schema",
      postgresql.JSONB(astext_type=sa.Text()),
      nullable=True,
    ),
    sa.CheckConstraint(
      f"name ~ '{_NAME_PATTERN}'",
      name="extensions_name_canonical",
    ),
    sa.CheckConstraint(
      f"version ~ '{_SEMVER_PATTERN}'",
      name="extensions_version_canonical",
    ),
    sa.PrimaryKeyConstraint("name"),
    schema=_PROTOCOL_SCHEMA,
  )


def _create_peer_enable_rpc() -> None:
  op.execute(
    f"""
    CREATE FUNCTION {_PROTOCOL_SCHEMA}.set_extension_peer_enabled(
      p_name text,
      p_peer_id uuid,
      p_enabled boolean
    )
    RETURNS SETOF {_PROTOCOL_SCHEMA}.extensions
    LANGUAGE sql
    VOLATILE
    STRICT
    SECURITY DEFINER
    SET search_path = pg_catalog, {_PROTOCOL_SCHEMA}
    AS $$
      UPDATE {_PROTOCOL_SCHEMA}.extensions
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
          FROM {_PROTOCOL_SCHEMA}.clients
          WHERE id = p_peer_id
        )
      RETURNING *
    $$
    """
  )
  op.execute(
    f"REVOKE EXECUTE ON FUNCTION "
    f"{_PROTOCOL_SCHEMA}.set_extension_peer_enabled(text, uuid, boolean) FROM PUBLIC"
  )


def _create_extension_state_guard() -> None:
  op.execute(
    f"""
    CREATE FUNCTION {_INTERNAL_SCHEMA}.enforce_extension_state_authority()
    RETURNS trigger
    LANGUAGE plpgsql
    SET search_path = pg_catalog
    AS $$
    BEGIN
      IF TG_OP = 'INSERT' AND cardinality(NEW.enabled) <> 0 THEN
        RAISE EXCEPTION 'extensions.enabled must be empty on insert'
          USING ERRCODE = '23514';
      END IF;
      IF TG_OP = 'UPDATE'
        AND cardinality(OLD.enabled) <> 0
        AND NEW.version IS DISTINCT FROM OLD.version
      THEN
        RAISE EXCEPTION 'cannot change extension version while peers are enabled'
          USING ERRCODE = '23514';
      END IF;
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
  op.execute(
    f"""
    CREATE TRIGGER extensions_state_authority
    BEFORE INSERT OR UPDATE OR DELETE ON {_PROTOCOL_SCHEMA}.extensions
    FOR EACH ROW
    EXECUTE FUNCTION {_INTERNAL_SCHEMA}.enforce_extension_state_authority()
    """
  )


def upgrade() -> None:
  """Reset exactly the three rejected Extension-state relations."""
  op.drop_table("extension_peer_bindings", schema=_PROTOCOL_SCHEMA)
  op.drop_table("extension_installations", schema=_PROTOCOL_SCHEMA)
  op.drop_table("extensions", schema=_PROTOCOL_SCHEMA)
  _create_canonical_extensions()
  _create_extension_state_guard()
  _create_peer_enable_rpc()


def _create_previous_extensions() -> None:
  op.create_table(
    "extensions",
    sa.Column("id", sa.Text(), nullable=False),
    sa.Column("version", sa.Text(), nullable=False),
    sa.Column(
      "enabled",
      postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
      server_default=sa.text("'{}'::uuid[]"),
      nullable=False,
    ),
    sa.Column("nickname", sa.Text(), nullable=True),
    sa.Column(
      "config",
      postgresql.JSONB(astext_type=sa.Text()),
      server_default=sa.text("'{}'::jsonb"),
      nullable=True,
    ),
    sa.Column("config_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.PrimaryKeyConstraint("id"),
    schema=_PROTOCOL_SCHEMA,
  )


def _create_previous_registry_state() -> None:
  coordinate_pattern = r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$"
  target_key_pattern = r"^[a-z0-9]([a-z0-9._-]{0,126}[a-z0-9])?$"
  target_digest_pattern = r"^sha256:[0-9a-f]{64}$"
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
      f"namespace ~ '{coordinate_pattern}'",
      name="extension_installations_namespace_canonical",
    ),
    sa.CheckConstraint(
      f"name ~ '{coordinate_pattern}'",
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
      f"namespace ~ '{coordinate_pattern}'",
      name="extension_peer_bindings_namespace_canonical",
    ),
    sa.CheckConstraint(
      f"name ~ '{coordinate_pattern}'",
      name="extension_peer_bindings_name_canonical",
    ),
    sa.CheckConstraint(
      f"version ~ '{_SEMVER_PATTERN}'",
      name="extension_peer_bindings_version_canonical",
    ),
    sa.CheckConstraint(
      f"target_key ~ '{target_key_pattern}'",
      name="extension_peer_bindings_target_key_canonical",
    ),
    sa.CheckConstraint(
      f"target_digest ~ '{target_digest_pattern}'",
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
  """Restore the prior empty schemas; row restoration requires the cutover snapshot."""
  op.execute(
    f"DROP FUNCTION {_PROTOCOL_SCHEMA}.set_extension_peer_enabled(text, uuid, boolean)"
  )
  op.drop_table("extensions", schema=_PROTOCOL_SCHEMA)
  op.execute(f"DROP FUNCTION {_INTERNAL_SCHEMA}.enforce_extension_state_authority()")
  _create_previous_extensions()
  _create_previous_registry_state()
