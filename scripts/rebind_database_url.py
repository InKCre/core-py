"""Build a role-specific database URL without logging any input credential."""

import argparse
import os
from urllib.parse import quote, urlsplit, urlunsplit


def rebind_database_url(
  source_url: str,
  *,
  role: str,
  password: str,
  scheme: str,
) -> str:
  """Keep branch/database/TLS coordinates while replacing the principal."""
  parsed = urlsplit(source_url)
  if (
    parsed.scheme not in {"postgres", "postgresql", "postgresql+psycopg"}
    or not parsed.hostname
    or not parsed.path
  ):
    raise ValueError("source is not a supported PostgreSQL URL")
  if not role or not password:
    raise ValueError("target role and password are required")
  if scheme not in {"postgresql", "postgresql+psycopg"}:
    raise ValueError("unsupported target URL scheme")

  host = parsed.hostname
  if ":" in host:
    host = f"[{host}]"
  port = f":{parsed.port}" if parsed.port is not None else ""
  authority = f"{quote(role, safe='')}:{quote(password, safe='')}@{host}{port}"
  return urlunsplit(
    (
      scheme,
      authority,
      parsed.path,
      parsed.query,
      parsed.fragment,
    )
  )


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--scheme",
    choices=("postgresql", "postgresql+psycopg"),
    required=True,
  )
  return parser


def main() -> int:
  args = build_parser().parse_args()
  source_url = os.getenv("SOURCE_DATABASE_URL", "")
  role = os.getenv("TARGET_DATABASE_ROLE", "")
  password = os.getenv("TARGET_DATABASE_PASSWORD", "")
  try:
    rebound = rebind_database_url(
      source_url,
      role=role,
      password=password,
      scheme=args.scheme,
    )
  except ValueError as exc:
    raise SystemExit(str(exc)) from None
  print(rebound)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
