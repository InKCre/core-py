"""CLI for the executable peer database lifecycle contract."""

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.database_contract.catalog import (
  reconcile_builtins,
  seed_development,
)
from app.database_contract.lifecycle import (
  contract_document,
  initialize,
  reset_development,
)
from app.database_contract.migration import migrate
from app.database_contract.readiness import check_database_contract
from app.database_contract.roles import RoleSecrets, provision_roles
from app.database_contract.schema_artifact import read_schema_manifest


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(prog="db")
  subcommands = parser.add_subparsers(dest="command", required=True)

  init_parser = subcommands.add_parser("init")
  init_parser.add_argument(
    "--profile",
    choices=("runtime", "development"),
    required=True,
  )
  init_parser.add_argument(
    "--environment",
    choices=("runtime", "preview", "production"),
  )

  subcommands.add_parser("migrate")
  subcommands.add_parser("provision-roles")
  subcommands.add_parser("reconcile-builtins")
  subcommands.add_parser("seed-dev")

  ready_parser = subcommands.add_parser("ready")
  ready_parser.add_argument(
    "--profile",
    choices=("runtime", "development"),
    default="runtime",
  )
  ready_parser.add_argument("--json", action="store_true")

  reset_parser = subcommands.add_parser("reset-dev")
  reset_parser.add_argument("--confirm", required=True)

  contract_parser = subcommands.add_parser("contract")
  contract_parser.add_argument("--json", action="store_true")
  schema_parser = subcommands.add_parser("schema")
  schema_parser.add_argument("--json", action="store_true")
  return parser


def _success(command: str) -> None:
  print(json.dumps({"status": "ok", "command": command}, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
  args = build_parser().parse_args(argv)
  try:
    if args.command == "init":
      initialize(args.profile, environment=args.environment)
      _success(args.command)
      return 0
    if args.command == "migrate":
      migrate()
      _success(args.command)
      return 0
    if args.command == "provision-roles":
      provision_roles(RoleSecrets.from_environment())
      _success(args.command)
      return 0
    if args.command == "reconcile-builtins":
      reconcile_builtins()
      _success(args.command)
      return 0
    if args.command == "seed-dev":
      seed_development()
      _success(args.command)
      return 0
    if args.command == "ready":
      readiness = check_database_contract(args.profile)
      if args.json:
        print(json.dumps(readiness.as_dict(), sort_keys=True))
      else:
        print(readiness.reason)
      return 0 if readiness.ready else 1
    if args.command == "reset-dev":
      reset_development(args.confirm)
      _success(args.command)
      return 0
    if args.command == "contract":
      document = contract_document()
      print(
        json.dumps(
          document,
          indent=None if args.json else 2,
          sort_keys=True,
        )
      )
      return 0
    if args.command == "schema":
      manifest = read_schema_manifest()
      print(
        json.dumps(
          manifest,
          indent=None if args.json else 2,
          sort_keys=True,
        )
      )
      return 0
  except Exception:
    print(
      json.dumps(
        {
          "status": "error",
          "command": args.command,
          "reason": "database_contract_operation_failed",
        },
        sort_keys=True,
      ),
      file=sys.stderr,
    )
    return 1
  raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
  raise SystemExit(main())
