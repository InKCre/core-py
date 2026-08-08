"""Create release metadata for a schema exported from a migrated database."""

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.database_contract.schema_artifact import write_schema_manifest


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser()
  parser.add_argument("--schema", type=Path, required=True)
  parser.add_argument("--roles", type=Path, required=True)
  parser.add_argument("--runtime-contract", type=Path, required=True)
  parser.add_argument("--output", type=Path, required=True)
  parser.add_argument("--source-revision", required=True)
  return parser


def main() -> None:
  args = build_parser().parse_args()
  write_schema_manifest(
    args.schema,
    args.roles,
    args.runtime_contract,
    args.output,
    args.source_revision,
  )


if __name__ == "__main__":
  main()
