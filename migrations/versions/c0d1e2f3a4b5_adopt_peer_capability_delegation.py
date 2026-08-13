"""adopt Peer capability advertisement and database-time leases

Revision ID: c0d1e2f3a4b5
Revises: b9c0d1e2f3a4
Create Date: 2026-08-07

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql

from app.database_contract import INTERNAL_SCHEMA, PROTOCOL_SCHEMA
from app.database_contract.constants import (
  CONTRACT_REVISION,
  JWT_AUDIENCE,
  JWT_ISSUER,
  JWT_MAX_LIFETIME_SECONDS,
  JWT_ROLE,
)


revision: str = "c0d1e2f3a4b5"
down_revision: str | Sequence[str] | None = "b9c0d1e2f3a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PREVIOUS_CONTRACT_REVISION = "peer-database-runtime-v2"
_PREVIOUS_JWT_ISSUER = "inkcre-client"


def _replace_check_jwt(issuer: str) -> None:
  op.execute(
    f"""
    CREATE OR REPLACE FUNCTION "{INTERNAL_SCHEMA}".check_jwt()
    RETURNS void
    LANGUAGE plpgsql
    SECURITY INVOKER
    SET search_path = pg_catalog
    AS $$
    DECLARE
      claims jsonb;
      issued_at numeric;
      expires_at numeric;
      current_epoch numeric := extract(epoch FROM statement_timestamp());
    BEGIN
      claims := nullif(current_setting('request.jwt.claims', true), '')::jsonb;

      IF claims IS NULL
         OR jsonb_typeof(claims -> 'role') <> 'string'
         OR claims ->> 'role' <> '{JWT_ROLE}'
         OR jsonb_typeof(claims -> 'iss') <> 'string'
         OR claims ->> 'iss' <> '{issuer}'
         OR jsonb_typeof(claims -> 'aud') <> 'string'
         OR claims ->> 'aud' <> '{JWT_AUDIENCE}'
         OR jsonb_typeof(claims -> 'iat') <> 'number'
         OR jsonb_typeof(claims -> 'exp') <> 'number'
      THEN
        RAISE insufficient_privilege USING MESSAGE = 'invalid jwt claims';
      END IF;

      issued_at := (claims ->> 'iat')::numeric;
      expires_at := (claims ->> 'exp')::numeric;
      IF issued_at > current_epoch + 60
         OR expires_at <= current_epoch
         OR expires_at <= issued_at
         OR expires_at - issued_at > {JWT_MAX_LIFETIME_SECONDS}
      THEN
        RAISE insufficient_privilege USING MESSAGE = 'invalid jwt lifetime';
      END IF;
    END
    $$
    """
  )


def upgrade() -> None:
  op.rename_table("clients", "peers", schema=PROTOCOL_SCHEMA)
  op.execute(
    f"""
    UPDATE "{PROTOCOL_SCHEMA}".peers
    SET labels = COALESCE(labels, ARRAY[]::text[]),
        config = COALESCE(config, '{{}}'::jsonb),
        config_schema = COALESCE(config_schema, '{{}}'::jsonb),
        created_at = COALESCE(created_at, statement_timestamp())
    """
  )
  for column in ("labels", "config", "config_schema", "created_at"):
    op.alter_column(
      "peers",
      column,
      existing_nullable=True,
      nullable=False,
      schema=PROTOCOL_SCHEMA,
    )
  op.drop_column("peers", "rest_api_url", schema=PROTOCOL_SCHEMA)
  op.add_column(
    "peers",
    sa.Column(
      "capabilities",
      sqlalchemy.dialects.postgresql.JSONB(astext_type=sa.Text()),
      server_default=sa.text("'[]'::jsonb"),
      nullable=False,
    ),
    schema=PROTOCOL_SCHEMA,
  )
  op.add_column(
    "peers",
    sa.Column("lease_expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
    schema=PROTOCOL_SCHEMA,
  )
  op.add_column(
    "peers",
    sa.Column(
      "updated_at",
      sa.TIMESTAMP(timezone=True),
      server_default=sa.text("CURRENT_TIMESTAMP"),
      nullable=False,
    ),
    schema=PROTOCOL_SCHEMA,
  )
  op.execute(
    f"""
    CREATE TRIGGER update_peers_updated_at
    BEFORE UPDATE ON "{PROTOCOL_SCHEMA}".peers
    FOR EACH ROW EXECUTE FUNCTION "{INTERNAL_SCHEMA}".update_updated_at_column()
    """
  )
  op.execute(
    f"""
    CREATE OR REPLACE FUNCTION "{PROTOCOL_SCHEMA}".renew_peer_lease(
      peer uuid,
      ttl_seconds integer
    )
    RETURNS timestamptz
    LANGUAGE plpgsql
    SECURITY INVOKER
    SET search_path = pg_catalog
    AS $$
    DECLARE
      renewed timestamptz;
    BEGIN
      IF ttl_seconds IS NULL OR ttl_seconds <= 0 THEN
        RAISE check_violation USING MESSAGE = 'peer lease TTL must be positive';
      END IF;
      UPDATE "{PROTOCOL_SCHEMA}".peers
      SET lease_expires_at = statement_timestamp() + make_interval(secs => ttl_seconds)
      WHERE id = peer
      RETURNING lease_expires_at INTO renewed;
      IF NOT FOUND THEN
        RAISE foreign_key_violation USING MESSAGE = 'peer does not exist';
      END IF;
      RETURN renewed;
    END
    $$
    """
  )
  _replace_check_jwt(JWT_ISSUER)
  op.execute(
    sa.text(
      f"""
      UPDATE "{INTERNAL_SCHEMA}".contract_state
      SET contract_revision = :revision,
          updated_at = statement_timestamp()
      WHERE singleton
      """
    ).bindparams(revision=CONTRACT_REVISION)
  )
  op.execute("NOTIFY pgrst, 'reload schema'")


def downgrade() -> None:
  op.execute(f'DROP FUNCTION IF EXISTS "{PROTOCOL_SCHEMA}".renew_peer_lease(uuid, integer)')
  op.execute(f'DROP TRIGGER IF EXISTS update_peers_updated_at ON "{PROTOCOL_SCHEMA}".peers')
  op.drop_column("peers", "updated_at", schema=PROTOCOL_SCHEMA)
  op.drop_column("peers", "lease_expires_at", schema=PROTOCOL_SCHEMA)
  op.drop_column("peers", "capabilities", schema=PROTOCOL_SCHEMA)
  op.add_column(
    "peers",
    sa.Column("rest_api_url", sa.Text(), nullable=True),
    schema=PROTOCOL_SCHEMA,
  )
  for column in ("labels", "config", "config_schema", "created_at"):
    op.alter_column(
      "peers",
      column,
      existing_nullable=False,
      nullable=True,
      schema=PROTOCOL_SCHEMA,
    )
  op.rename_table("peers", "clients", schema=PROTOCOL_SCHEMA)
  _replace_check_jwt(_PREVIOUS_JWT_ISSUER)
  op.execute(
    sa.text(
      f"""
      UPDATE "{INTERNAL_SCHEMA}".contract_state
      SET contract_revision = :revision,
          updated_at = statement_timestamp()
      WHERE singleton
      """
    ).bindparams(revision=_PREVIOUS_CONTRACT_REVISION)
  )
  op.execute("NOTIFY pgrst, 'reload schema'")
