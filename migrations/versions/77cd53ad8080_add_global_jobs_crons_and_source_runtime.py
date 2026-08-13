"""add global Jobs, Crons, and Source runtime contracts

Revision ID: 77cd53ad8080
Revises: c0d1e2f3a4b5
Create Date: 2026-08-10 23:33:32.200285

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql

from app.database_contract import INTERNAL_SCHEMA, PROTOCOL_SCHEMA
from app.database_contract.constants import CONTRACT_REVISION


# revision identifiers, used by Alembic.
revision: str = "77cd53ad8080"
down_revision: str | Sequence[str] | None = "c0d1e2f3a4b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
  op.add_column(
    "storage_types",
    sa.Column("writable", sa.Boolean(), server_default=sa.false(), nullable=False),
    schema=PROTOCOL_SCHEMA,
  )
  op.execute(
    f"""
    UPDATE "{PROTOCOL_SCHEMA}".storage_types
    SET writable = (id = 'postgresql_binary')
    """
  )

  op.add_column(
    "sources_types",
    sa.Column(
      "collect_config_schema",
      sqlalchemy.dialects.postgresql.JSONB(astext_type=sa.Text()),
      server_default=sa.text("'{}'::jsonb"),
      nullable=False,
    ),
    schema=PROTOCOL_SCHEMA,
  )
  op.add_column(
    "sources_types",
    sa.Column(
      "backfill_config_schema",
      sqlalchemy.dialects.postgresql.JSONB(astext_type=sa.Text()),
      nullable=True,
    ),
    schema=PROTOCOL_SCHEMA,
  )

  op.add_column(
    "sources",
    sa.Column("storage", sa.Integer(), nullable=True),
    schema=PROTOCOL_SCHEMA,
  )
  op.add_column(
    "sources",
    sa.Column("block", sa.Integer(), nullable=True),
    schema=PROTOCOL_SCHEMA,
  )
  op.add_column(
    "sources",
    sa.Column(
      "created_at",
      sa.TIMESTAMP(timezone=True),
      server_default=sa.text("CURRENT_TIMESTAMP"),
      nullable=False,
    ),
    schema=PROTOCOL_SCHEMA,
  )
  op.add_column(
    "sources",
    sa.Column(
      "updated_at",
      sa.TIMESTAMP(timezone=True),
      server_default=sa.text("CURRENT_TIMESTAMP"),
      nullable=False,
    ),
    schema=PROTOCOL_SCHEMA,
  )
  op.create_foreign_key(
    "sources_storage_fkey",
    "sources",
    "storages",
    ["storage"],
    ["id"],
    source_schema=PROTOCOL_SCHEMA,
    referent_schema=PROTOCOL_SCHEMA,
    onupdate="CASCADE",
    ondelete="RESTRICT",
  )
  op.create_foreign_key(
    "sources_block_fkey",
    "sources",
    "blocks",
    ["block"],
    ["id"],
    source_schema=PROTOCOL_SCHEMA,
    referent_schema=PROTOCOL_SCHEMA,
    onupdate="CASCADE",
    ondelete="SET NULL",
  )
  op.create_unique_constraint(
    "sources_block_key",
    "sources",
    ["block"],
    schema=PROTOCOL_SCHEMA,
  )
  op.drop_column("sources", "collect_at", schema=PROTOCOL_SCHEMA)

  op.drop_table("sources_collect_jobs", schema=PROTOCOL_SCHEMA)
  sa.Enum(name="sourcecollectjobstatus", schema=PROTOCOL_SCHEMA).drop(
    op.get_bind(),
    checkfirst=True,
  )

  op.create_table(
    "job_types",
    sa.Column("id", sa.Text(), nullable=False),
    sa.Column("description", sa.Text(), nullable=False),
    sa.Column(
      "parameters_schema",
      sqlalchemy.dialects.postgresql.JSONB(astext_type=sa.Text()),
      server_default=sa.text("'{}'::jsonb"),
      nullable=False,
    ),
    sa.Column("default_timeout_seconds", sa.Integer(), nullable=False),
    sa.CheckConstraint(
      "default_timeout_seconds > 0",
      name="job_types_default_timeout_seconds_positive",
    ),
    sa.PrimaryKeyConstraint("id"),
    schema=PROTOCOL_SCHEMA,
  )

  job_status = sqlalchemy.dialects.postgresql.ENUM(
    "pending",
    "running",
    "finished",
    "failed",
    "timed_out",
    "aborted",
    name="jobstatus",
    schema=PROTOCOL_SCHEMA,
    create_type=False,
  )
  job_status.create(op.get_bind(), checkfirst=True)
  op.create_table(
    "jobs",
    sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
    sa.Column("type", sa.Text(), nullable=False),
    sa.Column(
      "parameters",
      sqlalchemy.dialects.postgresql.JSONB(astext_type=sa.Text()),
      server_default=sa.text("'{}'::jsonb"),
      nullable=False,
    ),
    sa.Column(
      "state",
      sqlalchemy.dialects.postgresql.JSONB(astext_type=sa.Text()),
      server_default=sa.text("'{}'::jsonb"),
      nullable=False,
    ),
    sa.Column("timeout_seconds", sa.Integer(), nullable=False),
    sa.Column("status", job_status, server_default="pending", nullable=False),
    sa.Column(
      "created_at",
      sa.TIMESTAMP(timezone=True),
      server_default=sa.text("CURRENT_TIMESTAMP"),
      nullable=False,
    ),
    sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column("closed_at", sa.TIMESTAMP(timezone=True), nullable=True),
    sa.CheckConstraint("timeout_seconds > 0", name="jobs_timeout_seconds_positive"),
    sa.CheckConstraint(
      "(status = 'pending' AND started_at IS NULL AND closed_at IS NULL) OR "
      "(status = 'running' AND started_at IS NOT NULL AND closed_at IS NULL) OR "
      "(status IN ('finished', 'failed', 'timed_out', 'aborted') "
      "AND closed_at IS NOT NULL)",
      name="jobs_lifecycle_timestamps_valid",
    ),
    sa.ForeignKeyConstraint(
      ["type"],
      [f"{PROTOCOL_SCHEMA}.job_types.id"],
      onupdate="CASCADE",
      ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint("id"),
    schema=PROTOCOL_SCHEMA,
  )
  op.create_index(
    "jobs_status_idx",
    "jobs",
    ["status"],
    schema=PROTOCOL_SCHEMA,
  )
  op.execute(
    f"""
    CREATE OR REPLACE FUNCTION "{INTERNAL_SCHEMA}".set_job_lifecycle_timestamps()
    RETURNS trigger
    LANGUAGE plpgsql
    SECURITY INVOKER
    SET search_path = pg_catalog
    AS $$
    BEGIN
      IF NEW.status IS DISTINCT FROM OLD.status THEN
        IF OLD.status = 'pending' AND NEW.status = 'running' THEN
          NEW.started_at := statement_timestamp();
        ELSIF NEW.status IN ('finished', 'failed', 'timed_out', 'aborted') THEN
          NEW.closed_at := statement_timestamp();
        END IF;
      END IF;
      RETURN NEW;
    END
    $$
    """
  )
  op.execute(
    f"""
    CREATE TRIGGER set_jobs_lifecycle_timestamps
    BEFORE UPDATE ON "{PROTOCOL_SCHEMA}".jobs
    FOR EACH ROW EXECUTE FUNCTION "{INTERNAL_SCHEMA}".set_job_lifecycle_timestamps()
    """
  )

  op.create_table(
    "crons",
    sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
    sa.Column("schedule", sa.Text(), nullable=False),
    sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
    sa.Column("job_type", sa.Text(), nullable=False),
    sa.Column(
      "job_parameters",
      sqlalchemy.dialects.postgresql.JSONB(astext_type=sa.Text()),
      server_default=sa.text("'{}'::jsonb"),
      nullable=False,
    ),
    sa.Column("job_timeout_seconds", sa.Integer(), nullable=True),
    sa.Column("last_job", sa.BigInteger(), nullable=True),
    sa.Column("last_scheduled_for", sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column(
      "created_at",
      sa.TIMESTAMP(timezone=True),
      server_default=sa.text("CURRENT_TIMESTAMP"),
      nullable=False,
    ),
    sa.Column(
      "updated_at",
      sa.TIMESTAMP(timezone=True),
      server_default=sa.text("CURRENT_TIMESTAMP"),
      nullable=False,
    ),
    sa.CheckConstraint(
      "job_timeout_seconds IS NULL OR job_timeout_seconds > 0",
      name="crons_job_timeout_seconds_positive",
    ),
    sa.ForeignKeyConstraint(
      ["job_type"],
      [f"{PROTOCOL_SCHEMA}.job_types.id"],
      onupdate="CASCADE",
      ondelete="RESTRICT",
    ),
    sa.ForeignKeyConstraint(
      ["last_job"],
      [f"{PROTOCOL_SCHEMA}.jobs.id"],
      onupdate="CASCADE",
      ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint("id"),
    schema=PROTOCOL_SCHEMA,
  )
  op.create_index(
    "crons_enabled_idx",
    "crons",
    ["enabled"],
    schema=PROTOCOL_SCHEMA,
  )

  for table_name in ("sources", "crons"):
    op.execute(
      f"""
      CREATE TRIGGER update_{table_name}_updated_at
      BEFORE UPDATE ON "{PROTOCOL_SCHEMA}"."{table_name}"
      FOR EACH ROW EXECUTE FUNCTION "{INTERNAL_SCHEMA}".update_updated_at_column()
      """
    )

  op.execute(
    f"""
    CREATE OR REPLACE FUNCTION "{INTERNAL_SCHEMA}".enforce_source_storage_writable()
    RETURNS trigger
    LANGUAGE plpgsql
    SECURITY INVOKER
    SET search_path = pg_catalog
    AS $$
    BEGIN
      IF EXISTS (
        SELECT 1
        FROM "{PROTOCOL_SCHEMA}".sources AS source
        LEFT JOIN "{PROTOCOL_SCHEMA}".storages AS storage
          ON storage.id = source.storage
        LEFT JOIN "{PROTOCOL_SCHEMA}".storage_types AS storage_type
          ON storage_type.id = storage.type
        WHERE source.storage IS NOT NULL
          AND COALESCE(storage_type.writable, false) IS NOT true
      ) THEN
        RAISE check_violation
          USING MESSAGE = 'sources.storage must reference a writable Storage type';
      END IF;
      RETURN NEW;
    END
    $$
    """
  )
  for table_name, events in (
    ("sources", "INSERT OR UPDATE"),
    ("storages", "UPDATE"),
    ("storage_types", "UPDATE"),
  ):
    op.execute(
      f"""
      CREATE CONSTRAINT TRIGGER enforce_source_storage_writable_from_{table_name}
      AFTER {events} ON "{PROTOCOL_SCHEMA}"."{table_name}"
      DEFERRABLE INITIALLY IMMEDIATE
      FOR EACH ROW EXECUTE FUNCTION "{INTERNAL_SCHEMA}".enforce_source_storage_writable()
      """
    )

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
  for table_name in ("storage_types", "storages", "sources"):
    op.execute(
      f"DROP TRIGGER IF EXISTS enforce_source_storage_writable_from_{table_name} "
      f'ON "{PROTOCOL_SCHEMA}"."{table_name}"'
    )
  op.execute(
    f'DROP FUNCTION IF EXISTS "{INTERNAL_SCHEMA}".enforce_source_storage_writable()'
  )
  for table_name in ("crons", "sources"):
    op.execute(
      f"DROP TRIGGER IF EXISTS update_{table_name}_updated_at "
      f'ON "{PROTOCOL_SCHEMA}"."{table_name}"'
    )

  op.execute(
    f'DROP TRIGGER IF EXISTS set_jobs_lifecycle_timestamps '
    f'ON "{PROTOCOL_SCHEMA}".jobs'
  )
  op.execute(
    f'DROP FUNCTION IF EXISTS "{INTERNAL_SCHEMA}".set_job_lifecycle_timestamps()'
  )

  op.drop_index("crons_enabled_idx", table_name="crons", schema=PROTOCOL_SCHEMA)
  op.drop_table("crons", schema=PROTOCOL_SCHEMA)
  op.drop_index("jobs_status_idx", table_name="jobs", schema=PROTOCOL_SCHEMA)
  op.drop_table("jobs", schema=PROTOCOL_SCHEMA)
  op.drop_table("job_types", schema=PROTOCOL_SCHEMA)
  sa.Enum(name="jobstatus", schema=PROTOCOL_SCHEMA).drop(op.get_bind(), checkfirst=True)

  old_status = sqlalchemy.dialects.postgresql.ENUM(
    "pending",
    "running",
    "finished",
    "failed",
    name="sourcecollectjobstatus",
    schema=PROTOCOL_SCHEMA,
    create_type=False,
  )
  old_status.create(op.get_bind(), checkfirst=True)
  op.create_table(
    "sources_collect_jobs",
    sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
    sa.Column("source", sa.Integer(), nullable=True),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column("closed_at", sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column("status", old_status, server_default="pending", nullable=True),
    sa.Column("state", sqlalchemy.dialects.postgresql.JSONB(), nullable=True),
    sa.Column("config", sqlalchemy.dialects.postgresql.JSONB(), nullable=True),
    sa.ForeignKeyConstraint(
      ["source"],
      [f"{PROTOCOL_SCHEMA}.sources.id"],
      onupdate="CASCADE",
      ondelete="CASCADE",
    ),
    sa.PrimaryKeyConstraint("id"),
    schema=PROTOCOL_SCHEMA,
  )

  op.add_column(
    "sources",
    sa.Column("collect_at", sqlalchemy.dialects.postgresql.JSONB(), nullable=True),
    schema=PROTOCOL_SCHEMA,
  )
  op.drop_constraint("sources_block_key", "sources", schema=PROTOCOL_SCHEMA)
  op.drop_constraint("sources_block_fkey", "sources", schema=PROTOCOL_SCHEMA)
  op.drop_constraint("sources_storage_fkey", "sources", schema=PROTOCOL_SCHEMA)
  for column in ("updated_at", "created_at", "block", "storage"):
    op.drop_column("sources", column, schema=PROTOCOL_SCHEMA)
  op.drop_column("sources_types", "backfill_config_schema", schema=PROTOCOL_SCHEMA)
  op.drop_column("sources_types", "collect_config_schema", schema=PROTOCOL_SCHEMA)
  op.drop_column("storage_types", "writable", schema=PROTOCOL_SCHEMA)

  op.execute(
    sa.text(
      f"""
      UPDATE "{INTERNAL_SCHEMA}".contract_state
      SET contract_revision = :revision,
          updated_at = statement_timestamp()
      WHERE singleton
      """
    ).bindparams(revision="peer-database-runtime-v3")
  )
  op.execute("NOTIFY pgrst, 'reload schema'")
