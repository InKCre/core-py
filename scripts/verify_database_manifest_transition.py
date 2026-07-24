"""Verify that production convergence preserves the existing database rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

CATALOG_TABLES_ALLOWING_ADDITIONS = frozenset(
  {
    "extensions",
    "sources_types",
    "storage_types",
  }
)


def _table_counts(manifest: dict[str, object]) -> dict[str, int]:
  raw_counts = manifest.get("table_counts")
  if not isinstance(raw_counts, dict):
    raise ValueError("manifest table_counts must be an object")

  counts: dict[str, int] = {}
  for table, count in raw_counts.items():
    if (
      not isinstance(table, str)
      or not isinstance(count, int)
      or isinstance(count, bool)
      or count < 0
    ):
      raise ValueError("manifest table_counts must contain non-negative integers")
    counts[table] = count
  return counts


def verify_manifest_transition(
  before: dict[str, object],
  after: dict[str, object],
) -> list[dict[str, int | str]]:
  """Return allowed catalog additions or reject an unsafe transition."""
  if after.get("schema") != "inkcre":
    raise ValueError("converged manifest must use the inkcre schema")

  before_counts = _table_counts(before)
  after_counts = _table_counts(after)
  if before_counts.keys() != after_counts.keys():
    missing = sorted(before_counts.keys() - after_counts.keys())
    unexpected = sorted(after_counts.keys() - before_counts.keys())
    raise ValueError(
      json.dumps(
        {
          "missing_tables": missing,
          "unexpected_tables": unexpected,
        },
        sort_keys=True,
      )
    )

  additions: list[dict[str, int | str]] = []
  for table, before_count in sorted(before_counts.items()):
    after_count = after_counts[table]
    if after_count == before_count:
      continue
    if table in CATALOG_TABLES_ALLOWING_ADDITIONS and after_count > before_count:
      additions.append(
        {
          "after": after_count,
          "before": before_count,
          "delta": after_count - before_count,
          "table": table,
        }
      )
      continue
    raise ValueError(
      json.dumps(
        {
          "after": after_count,
          "before": before_count,
          "table": table,
        },
        sort_keys=True,
      )
    )

  return additions


def _read_manifest(path: Path) -> dict[str, object]:
  value = json.loads(path.read_text())
  if not isinstance(value, dict):
    raise ValueError("database manifest must be a JSON object")
  return cast(dict[str, object], value)


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("before", type=Path)
  parser.add_argument("after", type=Path)
  args = parser.parse_args()

  additions = verify_manifest_transition(
    _read_manifest(args.before),
    _read_manifest(args.after),
  )
  print(
    json.dumps(
      {
        "catalog_additions": additions,
        "status": "ok",
      },
      sort_keys=True,
    )
  )
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
