"""Verify that pdm.lock is compatible and current."""

from pathlib import Path
import sys

from _tooling import run_pdm


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
  """Run PDM's lock consistency check through a working executable."""
  result = run_pdm(["lock", "--check"], cwd=PROJECT_ROOT)
  if result is None:
    print("ERROR: PDM is unavailable", file=sys.stderr)
    return 1
  if result.returncode != 0:
    print("ERROR: pdm.lock is missing, stale, or incompatible", file=sys.stderr)
    if result.stderr:
      print(result.stderr.rstrip(), file=sys.stderr)
    return result.returncode

  print("pdm.lock is current")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
