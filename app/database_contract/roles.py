"""Portable database principals, memberships, ACLs, and default ACLs."""

from dataclasses import dataclass
import os

from psycopg import sql

from .connection import database_connection
from .constants import (
  ANONYMOUS_ROLE,
  AUTHENTICATED_ROLE,
  AUTHENTICATOR_ROLE,
  CORE_RUNTIME_ROLE,
  INTERNAL_SCHEMA,
  PROTOCOL_SCHEMA,
)


MINIMUM_DATABASE_PASSWORD_BYTES = 32


@dataclass(frozen=True)
class RoleSecrets:
  """Runtime-only passwords used to reconcile login principals."""

  authenticator_password: str
  core_runtime_password: str

  @classmethod
  def from_environment(cls) -> "RoleSecrets":
    authenticator = os.getenv("POSTGREST_DATABASE_PASSWORD", "")
    core_runtime = os.getenv("CORE_DATABASE_PASSWORD", "")
    missing = [
      name
      for name, value in (
        ("POSTGREST_DATABASE_PASSWORD", authenticator),
        ("CORE_DATABASE_PASSWORD", core_runtime),
      )
      if not value
    ]
    if missing:
      raise ValueError(f"missing runtime database secret: {', '.join(missing)}")
    for name, value in (
      ("POSTGREST_DATABASE_PASSWORD", authenticator),
      ("CORE_DATABASE_PASSWORD", core_runtime),
    ):
      if len(value.encode()) < MINIMUM_DATABASE_PASSWORD_BYTES:
        raise ValueError(f"{name} must be at least 32 bytes")
    return cls(
      authenticator_password=authenticator,
      core_runtime_password=core_runtime,
    )


def _role_attributes(cursor, role_name: str) -> tuple[bool, ...] | None:
  cursor.execute(
    """
    SELECT
      rolcanlogin,
      rolinherit,
      rolsuper,
      rolcreatedb,
      rolcreaterole,
      rolreplication,
      rolbypassrls
    FROM pg_roles
    WHERE rolname = %s
    """,
    (role_name,),
  )
  return cursor.fetchone()


def _role_attribute_sql(*, login: bool, inherit: bool) -> sql.Composed:
  return sql.SQL(" ").join(
    [
      sql.SQL("LOGIN" if login else "NOLOGIN"),
      sql.SQL("INHERIT" if inherit else "NOINHERIT"),
      sql.SQL("NOSUPERUSER"),
      sql.SQL("NOCREATEDB"),
      sql.SQL("NOCREATEROLE"),
      sql.SQL("NOREPLICATION"),
      sql.SQL("NOBYPASSRLS"),
    ]
  )


def _ensure_role(
  cursor,
  role_name: str,
  *,
  login: bool,
  inherit: bool,
  password: str | None = None,
) -> bool:
  """Create a role atomically with final attributes; return whether it was new."""
  if _role_attributes(cursor, role_name) is not None:
    return False
  statement = sql.SQL("CREATE ROLE {} WITH {}").format(
    sql.Identifier(role_name),
    _role_attribute_sql(login=login, inherit=inherit),
  )
  if password is not None:
    statement += sql.SQL(" PASSWORD {}").format(sql.Literal(password))
  cursor.execute(statement)
  return True


def _set_role_attributes(
  cursor,
  role_name: str,
  *,
  login: bool,
  inherit: bool,
  password: str | None = None,
) -> None:
  expected = (
    login,
    inherit,
    False,
    False,
    False,
    False,
    False,
  )
  if _role_attributes(cursor, role_name) == expected:
    if password is not None:
      cursor.execute(
        sql.SQL("ALTER ROLE {} WITH PASSWORD {}").format(
          sql.Identifier(role_name),
          sql.Literal(password),
        )
      )
    return
  statement = sql.SQL("ALTER ROLE {} WITH {}").format(
    sql.Identifier(role_name),
    _role_attribute_sql(login=login, inherit=inherit),
  )
  if password is not None:
    statement += sql.SQL(" PASSWORD {}").format(sql.Literal(password))
  cursor.execute(statement)


def _revoke_parent_memberships(cursor, member_role: str) -> None:
  cursor.execute(
    """
    SELECT parent.rolname
    FROM pg_auth_members AS membership
    JOIN pg_roles AS parent ON parent.oid = membership.roleid
    JOIN pg_roles AS member ON member.oid = membership.member
    WHERE member.rolname = %s
    """,
    (member_role,),
  )
  for (parent_role,) in cursor.fetchall():
    cursor.execute(
      sql.SQL("REVOKE {} FROM {}").format(
        sql.Identifier(parent_role),
        sql.Identifier(member_role),
      )
    )


def _grant_membership(cursor, granted_role: str, member_role: str) -> None:
  cursor.execute(
    sql.SQL("GRANT {} TO {}").format(
      sql.Identifier(granted_role),
      sql.Identifier(member_role),
    )
  )


def _reconcile_object_privileges(cursor) -> None:
  principals_without_direct_access = (
    "PUBLIC",
    ANONYMOUS_ROLE,
    AUTHENTICATOR_ROLE,
  )

  for principal in principals_without_direct_access:
    target = sql.SQL("PUBLIC") if principal == "PUBLIC" else sql.Identifier(principal)
    cursor.execute(
      sql.SQL("REVOKE ALL ON SCHEMA {} FROM {}").format(
        sql.Identifier(PROTOCOL_SCHEMA),
        target,
      )
    )
    cursor.execute(
      sql.SQL("REVOKE ALL ON ALL TABLES IN SCHEMA {} FROM {}").format(
        sql.Identifier(PROTOCOL_SCHEMA),
        target,
      )
    )
    cursor.execute(
      sql.SQL("REVOKE ALL ON ALL SEQUENCES IN SCHEMA {} FROM {}").format(
        sql.Identifier(PROTOCOL_SCHEMA),
        target,
      )
    )
    cursor.execute(
      sql.SQL("REVOKE ALL ON ALL FUNCTIONS IN SCHEMA {} FROM {}").format(
        sql.Identifier(PROTOCOL_SCHEMA),
        target,
      )
    )

  cursor.execute(
    sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
      sql.Identifier(PROTOCOL_SCHEMA),
      sql.Identifier(AUTHENTICATED_ROLE),
    )
  )
  cursor.execute(
    sql.SQL("GRANT ALL ON ALL TABLES IN SCHEMA {} TO {}").format(
      sql.Identifier(PROTOCOL_SCHEMA),
      sql.Identifier(AUTHENTICATED_ROLE),
    )
  )
  cursor.execute(
    sql.SQL("REVOKE UPDATE ON TABLE {}.extensions FROM {}").format(
      sql.Identifier(PROTOCOL_SCHEMA),
      sql.Identifier(AUTHENTICATED_ROLE),
    )
  )
  cursor.execute(
    sql.SQL(
      "GRANT UPDATE (version, nickname, config, config_schema) ON TABLE {}.extensions TO {}"
    ).format(
      sql.Identifier(PROTOCOL_SCHEMA),
      sql.Identifier(AUTHENTICATED_ROLE),
    )
  )
  cursor.execute(
    sql.SQL("GRANT UPDATE (state) ON TABLE {}.extensions TO {}").format(
      sql.Identifier(PROTOCOL_SCHEMA),
      sql.Identifier(CORE_RUNTIME_ROLE),
    )
  )
  cursor.execute(
    sql.SQL("GRANT ALL ON ALL SEQUENCES IN SCHEMA {} TO {}").format(
      sql.Identifier(PROTOCOL_SCHEMA),
      sql.Identifier(AUTHENTICATED_ROLE),
    )
  )
  cursor.execute(
    sql.SQL("GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA {} TO {}").format(
      sql.Identifier(PROTOCOL_SCHEMA),
      sql.Identifier(AUTHENTICATED_ROLE),
    )
  )

  for principal in (
    "PUBLIC",
    ANONYMOUS_ROLE,
    AUTHENTICATOR_ROLE,
    AUTHENTICATED_ROLE,
  ):
    target = sql.SQL("PUBLIC") if principal == "PUBLIC" else sql.Identifier(principal)
    cursor.execute(
      sql.SQL("REVOKE ALL ON ALL TABLES IN SCHEMA {} FROM {}").format(
        sql.Identifier(INTERNAL_SCHEMA),
        target,
      )
    )

  cursor.execute(
    sql.SQL("REVOKE ALL ON SCHEMA {} FROM PUBLIC, {}, {}").format(
      sql.Identifier(INTERNAL_SCHEMA),
      sql.Identifier(ANONYMOUS_ROLE),
      sql.Identifier(AUTHENTICATOR_ROLE),
    )
  )
  cursor.execute(
    sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
      sql.Identifier(INTERNAL_SCHEMA),
      sql.Identifier(AUTHENTICATED_ROLE),
    )
  )
  cursor.execute(
    sql.SQL("GRANT SELECT ON TABLE {}.contract_state TO {}").format(
      sql.Identifier(INTERNAL_SCHEMA),
      sql.Identifier(AUTHENTICATED_ROLE),
    )
  )
  cursor.execute(
    sql.SQL("GRANT SELECT ON TABLE public.alembic_version TO {}").format(
      sql.Identifier(AUTHENTICATED_ROLE)
    )
  )
  cursor.execute(
    sql.SQL("REVOKE ALL ON ALL FUNCTIONS IN SCHEMA {} FROM PUBLIC, {}, {}").format(
      sql.Identifier(INTERNAL_SCHEMA),
      sql.Identifier(ANONYMOUS_ROLE),
      sql.Identifier(AUTHENTICATOR_ROLE),
    )
  )
  cursor.execute(
    sql.SQL("GRANT EXECUTE ON FUNCTION {}.check_jwt() TO {}").format(
      sql.Identifier(INTERNAL_SCHEMA),
      sql.Identifier(AUTHENTICATED_ROLE),
    )
  )
  cursor.execute(
    sql.SQL("GRANT EXECUTE ON FUNCTION {}.update_updated_at_column() TO {}").format(
      sql.Identifier(INTERNAL_SCHEMA),
      sql.Identifier(AUTHENTICATED_ROLE),
    )
  )

  cursor.execute(
    sql.SQL("REVOKE CREATE ON SCHEMA public FROM PUBLIC, {}, {}, {}").format(
      sql.Identifier(ANONYMOUS_ROLE),
      sql.Identifier(AUTHENTICATOR_ROLE),
      sql.Identifier(AUTHENTICATED_ROLE),
    )
  )


def _reconcile_default_privileges(cursor, owner_role: str) -> None:
  owner = sql.Identifier(owner_role)
  schema = sql.Identifier(PROTOCOL_SCHEMA)
  authenticated = sql.Identifier(AUTHENTICATED_ROLE)
  anonymous = sql.Identifier(ANONYMOUS_ROLE)
  authenticator = sql.Identifier(AUTHENTICATOR_ROLE)

  statements = (
    sql.SQL(
      "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA {} "
      "REVOKE ALL ON TABLES FROM PUBLIC, {}, {}"
    ).format(owner, schema, anonymous, authenticator),
    sql.SQL(
      "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA {} GRANT ALL ON TABLES TO {}"
    ).format(owner, schema, authenticated),
    sql.SQL(
      "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA {} "
      "REVOKE ALL ON SEQUENCES FROM PUBLIC, {}, {}"
    ).format(owner, schema, anonymous, authenticator),
    sql.SQL(
      "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA {} GRANT ALL ON SEQUENCES TO {}"
    ).format(owner, schema, authenticated),
    sql.SQL(
      "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA {} "
      "REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC, {}, {}"
    ).format(owner, schema, anonymous, authenticator),
    sql.SQL(
      "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA {} GRANT EXECUTE ON FUNCTIONS TO {}"
    ).format(owner, schema, authenticated),
  )
  for statement in statements:
    cursor.execute(statement)


def provision_roles(
  secrets: RoleSecrets,
  database_url: str | None = None,
) -> None:
  """Converge fixed principals and database-local privileges."""
  with database_connection(database_url) as connection:
    with connection.cursor() as cursor:
      _ensure_role(
        cursor,
        AUTHENTICATED_ROLE,
        login=False,
        inherit=False,
      )
      _ensure_role(
        cursor,
        ANONYMOUS_ROLE,
        login=False,
        inherit=False,
      )
      _ensure_role(
        cursor,
        AUTHENTICATOR_ROLE,
        login=True,
        inherit=False,
        password=secrets.authenticator_password,
      )
      _ensure_role(
        cursor,
        CORE_RUNTIME_ROLE,
        login=True,
        inherit=True,
        password=secrets.core_runtime_password,
      )

      _revoke_parent_memberships(cursor, AUTHENTICATED_ROLE)
      _revoke_parent_memberships(cursor, ANONYMOUS_ROLE)
      _revoke_parent_memberships(cursor, AUTHENTICATOR_ROLE)
      _revoke_parent_memberships(cursor, CORE_RUNTIME_ROLE)

      _set_role_attributes(
        cursor,
        AUTHENTICATED_ROLE,
        login=False,
        inherit=False,
      )
      _set_role_attributes(
        cursor,
        ANONYMOUS_ROLE,
        login=False,
        inherit=False,
      )
      _set_role_attributes(
        cursor,
        AUTHENTICATOR_ROLE,
        login=True,
        inherit=False,
        password=secrets.authenticator_password,
      )
      _set_role_attributes(
        cursor,
        CORE_RUNTIME_ROLE,
        login=True,
        inherit=True,
        password=secrets.core_runtime_password,
      )
      _grant_membership(cursor, AUTHENTICATED_ROLE, AUTHENTICATOR_ROLE)
      _grant_membership(cursor, AUTHENTICATED_ROLE, CORE_RUNTIME_ROLE)

      cursor.execute(
        sql.SQL("SELECT owner_role FROM {}.contract_state WHERE singleton").format(
          sql.Identifier(INTERNAL_SCHEMA)
        )
      )
      owner_row = cursor.fetchone()
      if owner_row is None:
        raise RuntimeError("database contract owner is not initialized")
      owner_role = owner_row[0]

      _reconcile_object_privileges(cursor)
      _reconcile_default_privileges(cursor, owner_role)
