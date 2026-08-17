"""Machine-readable, read-only verification of the peer database contract."""

from dataclasses import dataclass
import datetime
from typing import Any

from psycopg import sql

from .connection import database_connection
from .constants import (
  ANONYMOUS_ROLE,
  APPLICATION_TABLES,
  AUTHENTICATED_ROLE,
  AUTHENTICATOR_ROLE,
  CONTRACT_FORMAT,
  CONTRACT_REVISION,
  CORE_RUNTIME_ROLE,
  DEVELOPMENT_PEER_ID,
  DEVELOPMENT_PEER_NAME,
  INTERNAL_SCHEMA,
  PROTOCOL_SCHEMA,
)
from .profile import (
  BUILTIN_AI_DIALECTS,
  BUILTIN_JOB_TYPES,
  BUILTIN_STORAGES,
  BUILTIN_STORAGE_TYPES,
)
from .migration import get_repository_heads
from .protocol import PROTOCOL_FUNCTIONS, protocol_database_function_signatures


TABLE_PRIVILEGES = {
  "DELETE",
  "INSERT",
  "MAINTAIN",
  "REFERENCES",
  "SELECT",
  "TRIGGER",
  "TRUNCATE",
  "UPDATE",
}
EXTENSIONS_TABLE_PRIVILEGES = TABLE_PRIVILEGES - {"UPDATE"}
EXTENSIONS_UPDATE_COLUMNS = {"config", "config_schema", "nickname", "version"}
CORE_EXTENSIONS_UPDATE_COLUMNS = {"state"}
SEQUENCE_PRIVILEGES = {"SELECT", "UPDATE", "USAGE"}


@dataclass(frozen=True)
class ContractReadiness:
  """Stable readiness result used by the CLI and HTTP runtime."""

  profile: str
  components: dict[str, dict[str, Any]]

  @property
  def ready(self) -> bool:
    return all(
      component.get("status") in {"ok", "not_required"}
      for component in self.components.values()
    )

  @property
  def reason(self) -> str:
    if self.ready:
      return "ready"
    for name, component in self.components.items():
      if component.get("status") not in {"ok", "not_required"}:
        return f"{name}_mismatch"
    return "database_contract_mismatch"

  def as_dict(self) -> dict[str, Any]:
    return {
      "format": CONTRACT_FORMAT,
      "status": "ok" if self.ready else "error",
      "profile": self.profile,
      "contract": {
        "revision": CONTRACT_REVISION,
      },
      **self.components,
    }


def _role_component(cursor) -> dict[str, Any]:
  expected = {
    AUTHENTICATED_ROLE: (False, False),
    ANONYMOUS_ROLE: (False, False),
    AUTHENTICATOR_ROLE: (True, False),
    CORE_RUNTIME_ROLE: (True, True),
  }
  cursor.execute(
    """
    SELECT
      rolname,
      rolcanlogin,
      rolinherit,
      rolsuper,
      rolcreatedb,
      rolcreaterole,
      rolreplication,
      rolbypassrls
    FROM pg_roles
    WHERE rolname = ANY(%s)
    """,
    (list(expected),),
  )
  actual = {row[0]: row[1:] for row in cursor.fetchall()}
  problems: list[str] = []
  for role_name, (login, inherit) in expected.items():
    attributes = actual.get(role_name)
    if attributes is None:
      problems.append(f"missing:{role_name}")
      continue
    if attributes != (login, inherit, False, False, False, False, False):
      problems.append(f"attributes:{role_name}")

  cursor.execute(
    """
    SELECT member.rolname, array_agg(parent.rolname ORDER BY parent.rolname)
    FROM pg_auth_members AS membership
    JOIN pg_roles AS parent ON parent.oid = membership.roleid
    JOIN pg_roles AS member ON member.oid = membership.member
    WHERE member.rolname = ANY(%s)
    GROUP BY member.rolname
    """,
    (list(expected),),
  )
  memberships = {role: tuple(parents) for role, parents in cursor.fetchall()}
  required_memberships = {
    AUTHENTICATED_ROLE: (),
    ANONYMOUS_ROLE: (),
    AUTHENTICATOR_ROLE: (AUTHENTICATED_ROLE,),
    CORE_RUNTIME_ROLE: (AUTHENTICATED_ROLE,),
  }
  for role_name, parents in required_memberships.items():
    if memberships.get(role_name, ()) != parents:
      problems.append(f"membership:{role_name}")

  return {
    "status": "ok" if not problems else "error",
    "problems": sorted(problems),
  }


def _relation_acl_rows(cursor, relation_kind: str) -> dict[tuple[str, str], set[str]]:
  cursor.execute(
    """
    SELECT
      class.relname,
      CASE
        WHEN access.grantee = 0 THEN 'PUBLIC'
        ELSE grantee.rolname
      END,
      access.privilege_type
    FROM pg_class AS class
    JOIN pg_namespace AS namespace ON namespace.oid = class.relnamespace
    CROSS JOIN LATERAL aclexplode(
      COALESCE(
        class.relacl,
        acldefault(
          CASE WHEN class.relkind = 'S' THEN 'S'::"char" ELSE 'r'::"char" END,
          class.relowner
        )
      )
    ) AS access
    LEFT JOIN pg_roles AS grantee ON grantee.oid = access.grantee
    WHERE namespace.nspname = %s
      AND class.relkind = %s
    """,
    (PROTOCOL_SCHEMA, relation_kind),
  )
  rows: dict[tuple[str, str], set[str]] = {}
  for object_name, grantee, privilege in cursor.fetchall():
    rows.setdefault((object_name, grantee), set()).add(privilege)
  return rows


def _function_acl_rows(cursor, schema_name: str) -> dict[tuple[str, str], set[str]]:
  cursor.execute(
    """
    SELECT
      procedure.proname,
      CASE
        WHEN access.grantee = 0 THEN 'PUBLIC'
        ELSE grantee.rolname
      END,
      access.privilege_type
    FROM pg_proc AS procedure
    JOIN pg_namespace AS namespace ON namespace.oid = procedure.pronamespace
    CROSS JOIN LATERAL aclexplode(
      COALESCE(procedure.proacl, acldefault('f', procedure.proowner))
    ) AS access
    LEFT JOIN pg_roles AS grantee ON grantee.oid = access.grantee
    WHERE namespace.nspname = %s
    """,
    (schema_name,),
  )
  rows: dict[tuple[str, str], set[str]] = {}
  for object_name, grantee, privilege in cursor.fetchall():
    rows.setdefault((object_name, grantee), set()).add(privilege)
  return rows


def _extension_update_column_acl(cursor, role: str) -> set[str]:
  cursor.execute(
    """
    SELECT column_name
    FROM information_schema.column_privileges
    WHERE table_schema = %s
      AND table_name = 'extensions'
      AND grantee = %s
      AND privilege_type = 'UPDATE'
    """,
    (PROTOCOL_SCHEMA, role),
  )
  return {row[0] for row in cursor.fetchall()}


def _default_acl_rows(cursor, owner_role: str) -> dict[tuple[str, str], set[str]]:
  cursor.execute(
    """
    SELECT
      defaults.defaclobjtype::text,
      CASE
        WHEN access.grantee = 0 THEN 'PUBLIC'
        ELSE grantee.rolname
      END,
      access.privilege_type
    FROM pg_default_acl AS defaults
    JOIN pg_roles AS owner ON owner.oid = defaults.defaclrole
    JOIN pg_namespace AS namespace ON namespace.oid = defaults.defaclnamespace
    CROSS JOIN LATERAL aclexplode(defaults.defaclacl) AS access
    LEFT JOIN pg_roles AS grantee ON grantee.oid = access.grantee
    WHERE owner.rolname = %s
      AND namespace.nspname = %s
    """,
    (owner_role, PROTOCOL_SCHEMA),
  )
  rows: dict[tuple[str, str], set[str]] = {}
  for object_type, grantee, privilege in cursor.fetchall():
    rows.setdefault((object_type, grantee), set()).add(privilege)
  return rows


def _privilege_component(cursor, owner_role: str) -> dict[str, Any]:
  problems: list[str] = []

  cursor.execute(
    """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = %s
      AND table_type = 'BASE TABLE'
    ORDER BY table_name
    """,
    (PROTOCOL_SCHEMA,),
  )
  tables = tuple(row[0] for row in cursor.fetchall())
  if tables != tuple(sorted(APPLICATION_TABLES)):
    problems.append("protocol_tables")

  table_acls = _relation_acl_rows(cursor, "r")
  for table_name in APPLICATION_TABLES:
    expected_privileges = (
      EXTENSIONS_TABLE_PRIVILEGES if table_name == "extensions" else TABLE_PRIVILEGES
    )
    if table_acls.get((table_name, AUTHENTICATED_ROLE), set()) != expected_privileges:
      problems.append(f"table_acl:{table_name}")
    for denied in ("PUBLIC", ANONYMOUS_ROLE, AUTHENTICATOR_ROLE):
      if table_acls.get((table_name, denied)):
        problems.append(f"table_acl:{table_name}:{denied}")
  if _extension_update_column_acl(cursor, AUTHENTICATED_ROLE) != EXTENSIONS_UPDATE_COLUMNS:
    problems.append("column_acl:extensions:update")
  if (
    _extension_update_column_acl(cursor, CORE_RUNTIME_ROLE)
    != CORE_EXTENSIONS_UPDATE_COLUMNS
  ):
    problems.append("column_acl:extensions:core_runtime_update")

  sequence_acls = _relation_acl_rows(cursor, "S")
  cursor.execute(
    """
    SELECT class.relname
    FROM pg_class AS class
    JOIN pg_namespace AS namespace ON namespace.oid = class.relnamespace
    WHERE namespace.nspname = %s
      AND class.relkind = 'S'
    ORDER BY class.relname
    """,
    (PROTOCOL_SCHEMA,),
  )
  sequence_names = [row[0] for row in cursor.fetchall()]
  for sequence_name in sequence_names:
    if sequence_acls.get((sequence_name, AUTHENTICATED_ROLE), set()) != SEQUENCE_PRIVILEGES:
      problems.append(f"sequence_acl:{sequence_name}")
    for denied in ("PUBLIC", ANONYMOUS_ROLE, AUTHENTICATOR_ROLE):
      if sequence_acls.get((sequence_name, denied)):
        problems.append(f"sequence_acl:{sequence_name}:{denied}")

  protocol_functions = _function_acl_rows(cursor, PROTOCOL_SCHEMA)
  cursor.execute(
    """
    SELECT
      procedure.proname,
      procedure.proargnames,
      ARRAY(
        SELECT format_type(argument.type_oid, NULL)
        FROM unnest(procedure.proargtypes::oid[]) WITH ORDINALITY
          AS argument(type_oid, position)
        ORDER BY argument.position
      ),
      format_type(procedure.prorettype, NULL),
      procedure.proretset,
      procedure.provolatile
    FROM pg_proc AS procedure
    JOIN pg_namespace AS namespace ON namespace.oid = procedure.pronamespace
    WHERE namespace.nspname = %s
    ORDER BY procedure.proname
    """,
    (PROTOCOL_SCHEMA,),
  )
  protocol_function_rows = cursor.fetchall()
  protocol_function_names = [row[0] for row in protocol_function_rows]
  expected_function_signatures = protocol_database_function_signatures()
  actual_function_signatures = {
    function_name: (
      tuple(argument_names or ()),
      tuple(argument_types),
      return_type,
      returns_set,
      volatility,
    )
    for (
      function_name,
      argument_names,
      argument_types,
      return_type,
      returns_set,
      volatility,
    ) in protocol_function_rows
  }
  if protocol_function_names != sorted(PROTOCOL_FUNCTIONS):
    problems.append("protocol_functions")
  elif actual_function_signatures != expected_function_signatures:
    problems.append("protocol_function_signatures")
  for function_name in protocol_function_names:
    if protocol_functions.get((function_name, AUTHENTICATED_ROLE)) != {"EXECUTE"}:
      problems.append(f"function_acl:{function_name}")
    for denied in ("PUBLIC", ANONYMOUS_ROLE, AUTHENTICATOR_ROLE):
      if protocol_functions.get((function_name, denied)):
        problems.append(f"function_acl:{function_name}:{denied}")

  cursor.execute(
    """
    SELECT
      procedure.provolatile = 'v',
      procedure.proisstrict,
      procedure.prosecdef,
      pg_get_function_result(procedure.oid) = 'SETOF inkcre.extensions',
      procedure.proconfig = ARRAY['search_path=pg_catalog, inkcre']::text[]
    FROM pg_proc AS procedure
    WHERE procedure.oid =
      to_regprocedure('inkcre.set_extension_peer_enabled(text,uuid,boolean)')
    """
  )
  if cursor.fetchone() != (True, True, True, True, True):
    problems.append("set_extension_peer_enabled_signature")

  cursor.execute(
    """
    SELECT
      procedure.prosecdef,
      procedure.proconfig = ARRAY['search_path=pg_catalog']::text[]
    FROM pg_proc AS procedure
    WHERE procedure.oid =
      to_regprocedure('inkcre_internal.enforce_extension_state_authority()')
    """
  )
  if cursor.fetchone() != (False, True):
    problems.append("extension_state_authority_signature")

  internal_functions = _function_acl_rows(cursor, INTERNAL_SCHEMA)
  for function_name in ("check_jwt", "update_updated_at_column"):
    if internal_functions.get((function_name, AUTHENTICATED_ROLE)) != {"EXECUTE"}:
      problems.append(f"internal_function_acl:{function_name}")
    for denied in ("PUBLIC", ANONYMOUS_ROLE, AUTHENTICATOR_ROLE):
      if internal_functions.get((function_name, denied)):
        problems.append(f"internal_function_acl:{function_name}:{denied}")

  cursor.execute(
    """
    SELECT
      has_schema_privilege(%s, %s, 'USAGE'),
      has_schema_privilege(%s, %s, 'USAGE'),
      has_schema_privilege(%s, %s, 'USAGE'),
      has_schema_privilege(%s, %s, 'USAGE'),
      has_table_privilege(%s, %s, 'SELECT'),
      has_table_privilege(%s, 'public.alembic_version', 'SELECT')
    """,
    (
      AUTHENTICATED_ROLE,
      PROTOCOL_SCHEMA,
      ANONYMOUS_ROLE,
      PROTOCOL_SCHEMA,
      AUTHENTICATOR_ROLE,
      PROTOCOL_SCHEMA,
      AUTHENTICATED_ROLE,
      INTERNAL_SCHEMA,
      AUTHENTICATED_ROLE,
      f"{INTERNAL_SCHEMA}.contract_state",
      AUTHENTICATED_ROLE,
    ),
  )
  (
    authenticated_usage,
    anonymous_usage,
    authenticator_usage,
    internal_usage,
    internal_table_read,
    lineage_table_read,
  ) = cursor.fetchone()
  if (
    not authenticated_usage
    or anonymous_usage
    or authenticator_usage
    or not internal_usage
    or not internal_table_read
    or not lineage_table_read
  ):
    problems.append("schema_acl")

  defaults = _default_acl_rows(cursor, owner_role)
  for object_type, required in (
    ("r", TABLE_PRIVILEGES),
    ("S", SEQUENCE_PRIVILEGES),
    ("f", {"EXECUTE"}),
  ):
    if defaults.get((object_type, AUTHENTICATED_ROLE), set()) != required:
      problems.append(f"default_acl:{object_type}")
    for denied in ("PUBLIC", ANONYMOUS_ROLE, AUTHENTICATOR_ROLE):
      if defaults.get((object_type, denied)):
        problems.append(f"default_acl:{object_type}:{denied}")

  return {
    "status": "ok" if not problems else "error",
    "problems": sorted(set(problems)),
  }


def _catalog_component(cursor) -> dict[str, Any]:
  problems: list[str] = []

  for profile in BUILTIN_AI_DIALECTS:
    cursor.execute(
      sql.SQL("SELECT description, config_schema FROM {}.ai_dialects WHERE id = %s").format(
        sql.Identifier(PROTOCOL_SCHEMA)
      ),
      (profile.id,),
    )
    if cursor.fetchone() != (profile.description, profile.config_schema):
      problems.append(f"ai_dialects:{profile.id}")

  for profile in BUILTIN_STORAGE_TYPES:
    cursor.execute(
      sql.SQL(
        "SELECT description, config_schema, writable FROM {}.storage_types WHERE id = %s"
      ).format(sql.Identifier(PROTOCOL_SCHEMA)),
      (profile.id,),
    )
    if cursor.fetchone() != (
      profile.description,
      profile.config_schema,
      profile.writable,
    ):
      problems.append(f"storage_types:{profile.id}")

  for profile in BUILTIN_JOB_TYPES:
    cursor.execute(
      sql.SQL(
        "SELECT description, parameters_schema, default_timeout_seconds "
        "FROM {}.job_types WHERE id = %s"
      ).format(sql.Identifier(PROTOCOL_SCHEMA)),
      (profile.id,),
    )
    if cursor.fetchone() != (
      profile.description,
      profile.parameters_schema,
      profile.default_timeout_seconds,
    ):
      problems.append(f"job_types:{profile.id}")

  for storage in BUILTIN_STORAGES:
    cursor.execute(
      sql.SQL("SELECT type, nickname, config FROM {}.storages WHERE id = %s").format(
        sql.Identifier(PROTOCOL_SCHEMA)
      ),
      (storage.id,),
    )
    if cursor.fetchone() != (storage.type, storage.nickname, storage.config):
      problems.append(f"storage:{storage.id}")

  return {
    "status": "ok" if not problems else "error",
    "problems": sorted(problems),
  }


def _seed_component(cursor, profile: str) -> dict[str, Any]:
  if profile != "development":
    return {"status": "not_required"}
  cursor.execute(
    sql.SQL(
      "SELECT name, labels, config, config_schema, capabilities, "
      "lease_expires_at, created_at, updated_at "
      "FROM {}.peers WHERE id = %s"
    ).format(sql.Identifier(PROTOCOL_SCHEMA)),
    (DEVELOPMENT_PEER_ID,),
  )
  row = cursor.fetchone()
  expected = (
    DEVELOPMENT_PEER_NAME,
    ["development", "canonical-seed"],
    {},
    {},
    [],
    None,
    datetime.datetime(2000, 1, 1, tzinfo=datetime.UTC),
  )
  stable_row = row[:-1] if row is not None else None
  updated_at = row[-1] if row is not None else None
  return {
    "status": "ok" if stable_row == expected and updated_at is not None else "error",
    "problems": (
      [] if stable_row == expected and updated_at is not None else ["development_peer"]
    ),
  }


def check_database_contract(
  profile: str = "runtime",
  database_url: str | None = None,
) -> ContractReadiness:
  """Validate the complete database contract without mutating it."""
  if profile not in {"runtime", "development"}:
    raise ValueError(f"unsupported readiness profile: {profile}")

  expected_heads = get_repository_heads()
  components: dict[str, dict[str, Any]] = {
    "database": {"status": "error"},
    "migration": {
      "status": "error",
      "current": [],
      "expected": list(expected_heads),
    },
    "roles": {"status": "error", "problems": ["not_checked"]},
    "privileges": {"status": "error", "problems": ["not_checked"]},
    "catalog": {"status": "error", "problems": ["not_checked"]},
    "seed": {"status": "error", "problems": ["not_checked"]},
  }

  try:
    with database_connection(database_url) as connection:
      with connection.cursor() as cursor:
        cursor.execute("SELECT version_num FROM alembic_version ORDER BY version_num")
        current_heads = tuple(row[0] for row in cursor.fetchall())
        components["migration"] = {
          "status": "ok" if current_heads == expected_heads else "error",
          "current": list(current_heads),
          "expected": list(expected_heads),
        }

        cursor.execute(
          sql.SQL(
            "SELECT contract_revision, environment, owner_role "
            "FROM {}.contract_state WHERE singleton"
          ).format(sql.Identifier(INTERNAL_SCHEMA))
        )
        contract_state = cursor.fetchone()
        if contract_state is None:
          raise RuntimeError("database contract state is missing")
        revision, environment, owner_role = contract_state
        expected_environment = "development" if profile == "development" else None
        database_ok = revision == CONTRACT_REVISION and (
          expected_environment is None or environment == expected_environment
        )
        components["database"] = {
          "status": "ok" if database_ok else "error",
          "environment": environment,
        }
        components["roles"] = _role_component(cursor)
        components["privileges"] = _privilege_component(cursor, owner_role)
        components["catalog"] = _catalog_component(cursor)
        components["seed"] = _seed_component(cursor, profile)
  except Exception:
    components["database"] = {
      "status": "error",
      "reason": "unreachable_or_contract_unavailable",
    }

  return ContractReadiness(profile=profile, components=components)
