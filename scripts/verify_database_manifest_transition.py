"""Verify that production convergence preserves the existing database rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import cast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.database_contract.constants import (
  APPLICATION_TABLES,
  EXTENSION_CUTOVER_CURRENT_HEAD,
  EXTENSION_CUTOVER_PREVIOUS_HEAD,
  EXTENSION_CUTOVER_RELATIONS,
)

CATALOG_TABLES_ALLOWING_ADDITIONS = frozenset(
  {
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


def _alembic_heads(manifest: dict[str, object]) -> tuple[str, ...]:
  raw_heads = manifest.get("alembic_heads")
  if (
    not isinstance(raw_heads, list)
    or not raw_heads
    or any(not isinstance(head, str) or not head for head in raw_heads)
    or len(raw_heads) != len(set(raw_heads))
  ):
    raise ValueError("manifest alembic_heads must contain unique non-empty strings")
  return tuple(sorted(raw_heads))


def verify_manifest_transition(
  before: dict[str, object],
  after: dict[str, object],
) -> list[dict[str, int | str]]:
  """Return allowed catalog additions or reject an unsafe transition."""
  if before.get("schema") != "inkcre":
    raise ValueError("source manifest must use the inkcre schema")
  if after.get("schema") != "inkcre":
    raise ValueError("converged manifest must use the inkcre schema")

  before_counts = _table_counts(before)
  after_counts = _table_counts(after)
  before_heads = _alembic_heads(before)
  after_heads = _alembic_heads(after)
  expected_tables = set(APPLICATION_TABLES)
  previous_tables = expected_tables | (EXTENSION_CUTOVER_RELATIONS - {"extensions"})
  before_tables = set(before_counts)
  after_tables = set(after_counts)
  expected_before_tables = (
    previous_tables
    if before_heads == (EXTENSION_CUTOVER_PREVIOUS_HEAD,)
    else expected_tables
  )
  missing = sorted(expected_tables - after_tables)
  unexpected = sorted((before_tables | after_tables) - expected_tables)
  before_missing = sorted(expected_before_tables - before_tables)
  valid_before_head = before_heads in {
    (EXTENSION_CUTOVER_PREVIOUS_HEAD,),
    (EXTENSION_CUTOVER_CURRENT_HEAD,),
  }
  valid_after_head = after_heads == (EXTENSION_CUTOVER_CURRENT_HEAD,)
  valid_before = valid_before_head and before_tables == expected_before_tables
  valid_after = valid_after_head and after_tables == expected_tables
  hard_cut = before_heads == (EXTENSION_CUTOVER_PREVIOUS_HEAD,)
  extension_reset_invalid = hard_cut and after_counts.get("extensions") != 0
  if not valid_before or not valid_after or extension_reset_invalid:
    raise ValueError(
      json.dumps(
        {
          "after_alembic_heads": list(after_heads),
          "before_missing_tables": before_missing,
          "before_alembic_heads": list(before_heads),
          "missing_tables": missing,
          "extension_reset_invalid": extension_reset_invalid,
          "unexpected_tables": unexpected,
        },
        sort_keys=True,
      )
    )

  additions: list[dict[str, int | str]] = []
  for table, before_count in sorted(before_counts.items()):
    if hard_cut and table in EXTENSION_CUTOVER_RELATIONS:
      continue
    if table not in after_counts:
      raise ValueError(f"unexpected removed table outside hard cut: {table}")
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
