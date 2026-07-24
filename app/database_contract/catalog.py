"""Deterministic catalog, seed, and development reset operations."""

from hashlib import sha256
import json

from psycopg import sql
from psycopg.types.json import Jsonb

from .connection import database_connection
from .constants import (
  APPLICATION_TABLES,
  CONTRACT_REVISION,
  DATABASE_ENVIRONMENTS,
  DEVELOPMENT_CLIENT_ID,
  DEVELOPMENT_CLIENT_NAME,
  INTERNAL_SCHEMA,
  PROTOCOL_SCHEMA,
)
from .profile import (
  BUILTIN_EXTENSIONS,
  BUILTIN_SOURCE_TYPES,
  BUILTIN_STORAGES,
  BUILTIN_STORAGE_TYPES,
)


def configure_environment(
  environment: str,
  database_url: str | None = None,
) -> None:
  """Set an immutable database environment identity after migration."""
  if environment not in DATABASE_ENVIRONMENTS:
    raise ValueError(f"unsupported database environment: {environment}")

  with database_connection(database_url) as connection:
    with connection.cursor() as cursor:
      cursor.execute(
        sql.SQL(
          "SELECT environment FROM {}.contract_state WHERE singleton FOR UPDATE"
        ).format(sql.Identifier(INTERNAL_SCHEMA))
      )
      row = cursor.fetchone()
      if row is None:
        raise RuntimeError("database contract state is not initialized")
      current = row[0]
      if current not in {"runtime", environment}:
        raise ValueError(
          f"database environment is immutable: {current} cannot become {environment}"
        )
      cursor.execute(
        sql.SQL(
          "UPDATE {}.contract_state "
          "SET environment = %s, contract_revision = %s, "
          "updated_at = CURRENT_TIMESTAMP "
          "WHERE singleton"
        ).format(sql.Identifier(INTERNAL_SCHEMA)),
        (environment, CONTRACT_REVISION),
      )


def reconcile_builtins(database_url: str | None = None) -> None:
  """Upsert artifact-owned catalogs without starting any runtime service."""
  with database_connection(database_url) as connection:
    with connection.cursor() as cursor:
      for extension in BUILTIN_EXTENSIONS:
        cursor.execute(
          sql.SQL(
            """
            INSERT INTO {}.extensions (
              id, version, enabled, nickname, config, config_schema
            )
            VALUES (
              %s,
              %s,
              ARRAY[]::uuid[],
              %s,
              jsonb_build_object(),
              NULL
            )
            ON CONFLICT (id) DO UPDATE
            SET version = EXCLUDED.version,
                nickname = EXCLUDED.nickname
            """
          ).format(sql.Identifier(PROTOCOL_SCHEMA)),
          (extension.id, extension.version, extension.nickname),
        )

      for storage_type in BUILTIN_STORAGE_TYPES:
        cursor.execute(
          sql.SQL(
            """
            INSERT INTO {}.storage_types (id, description, config_schema)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE
            SET description = EXCLUDED.description,
                config_schema = EXCLUDED.config_schema
            """
          ).format(sql.Identifier(PROTOCOL_SCHEMA)),
          (
            storage_type.id,
            storage_type.description,
            Jsonb(storage_type.config_schema),
          ),
        )

      for source_type in BUILTIN_SOURCE_TYPES:
        cursor.execute(
          sql.SQL(
            """
            INSERT INTO {}.sources_types (id, description, config_schema)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE
            SET description = EXCLUDED.description,
                config_schema = EXCLUDED.config_schema
            """
          ).format(sql.Identifier(PROTOCOL_SCHEMA)),
          (
            source_type.id,
            source_type.description,
            Jsonb(source_type.config_schema),
          ),
        )

      for storage in BUILTIN_STORAGES:
        cursor.execute(
          sql.SQL(
            """
            INSERT INTO {}.storages (id, type, nickname, config)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE
            SET type = EXCLUDED.type,
                nickname = EXCLUDED.nickname,
                config = EXCLUDED.config
            """
          ).format(sql.Identifier(PROTOCOL_SCHEMA)),
          (storage.id, storage.type, storage.nickname, Jsonb(storage.config)),
        )


def _require_development(cursor) -> None:
  cursor.execute(
    sql.SQL("SELECT environment FROM {}.contract_state WHERE singleton").format(
      sql.Identifier(INTERNAL_SCHEMA)
    )
  )
  row = cursor.fetchone()
  if row is None or row[0] != "development":
    raise ValueError("operation requires a development database identity")


def seed_development(database_url: str | None = None) -> None:
  """Upsert the minimum stable development/E2E client baseline."""
  with database_connection(database_url) as connection:
    with connection.cursor() as cursor:
      _require_development(cursor)
      cursor.execute(
        sql.SQL(
          """
          INSERT INTO {}.clients (
            id,
            name,
            labels,
            rest_api_url,
            config,
            config_schema,
            created_at
          )
          VALUES (
            %s,
            %s,
            ARRAY['development', 'canonical-seed']::text[],
            NULL,
            jsonb_build_object(),
            jsonb_build_object(),
            '2000-01-01T00:00:00Z'::timestamptz
          )
          ON CONFLICT (id) DO UPDATE
          SET name = EXCLUDED.name,
              labels = EXCLUDED.labels,
              rest_api_url = EXCLUDED.rest_api_url,
              config = EXCLUDED.config,
              config_schema = EXCLUDED.config_schema,
              created_at = EXCLUDED.created_at
          """
        ).format(sql.Identifier(PROTOCOL_SCHEMA)),
        (DEVELOPMENT_CLIENT_ID, DEVELOPMENT_CLIENT_NAME),
      )


def truncate_development(database_url: str | None = None) -> None:
  """Delete application rows only after proving the database is development."""
  with database_connection(database_url) as connection:
    with connection.cursor() as cursor:
      _require_development(cursor)
      relations = sql.SQL(", ").join(
        sql.SQL("{}.{}").format(
          sql.Identifier(PROTOCOL_SCHEMA),
          sql.Identifier(table_name),
        )
        for table_name in APPLICATION_TABLES
      )
      cursor.execute(
        sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(relations)
      )


def development_baseline_fingerprint(
  database_url: str | None = None,
) -> str:
  """Return a value-safe fingerprint of deterministic baseline records."""
  with database_connection(database_url) as connection:
    with connection.cursor() as cursor:
      _require_development(cursor)
      document: dict[str, object] = {}
      for key, query in (
        (
          "extensions",
          sql.SQL("SELECT id, version, nickname FROM {}.extensions ORDER BY id").format(
            sql.Identifier(PROTOCOL_SCHEMA)
          ),
        ),
        (
          "storage_types",
          sql.SQL(
            "SELECT id, description, config_schema FROM {}.storage_types ORDER BY id"
          ).format(sql.Identifier(PROTOCOL_SCHEMA)),
        ),
        (
          "source_types",
          sql.SQL(
            "SELECT id, description, config_schema FROM {}.sources_types ORDER BY id"
          ).format(sql.Identifier(PROTOCOL_SCHEMA)),
        ),
        (
          "storages",
          sql.SQL("SELECT id, type, nickname, config FROM {}.storages ORDER BY id").format(
            sql.Identifier(PROTOCOL_SCHEMA)
          ),
        ),
        (
          "development_client",
          sql.SQL(
            "SELECT id::text, name, labels, rest_api_url, config, "
            "config_schema, created_at::text "
            "FROM {}.clients WHERE id = %s"
          ).format(sql.Identifier(PROTOCOL_SCHEMA)),
        ),
      ):
        if key == "development_client":
          cursor.execute(query, (DEVELOPMENT_CLIENT_ID,))
        else:
          cursor.execute(query)
        document[key] = cursor.fetchall()

  encoded = json.dumps(
    document,
    default=str,
    separators=(",", ":"),
    sort_keys=True,
  ).encode()
  return sha256(encoded).hexdigest()
