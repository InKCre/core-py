"""Verify that pdm.lock is compatible and current."""

from pathlib import Path
import sys
import tomllib

from _tooling import run_pdm


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _missing_dependency_groups() -> set[str]:
  project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
  lock = tomllib.loads((PROJECT_ROOT / "pdm.lock").read_text())
  declared = set(project.get("dependency-groups", {}))
  locked = set(lock.get("metadata", {}).get("groups", []))
  return declared - locked


def main() -> int:
  """Run PDM's lock consistency check through a working executable."""
  missing_groups = _missing_dependency_groups()
  if missing_groups:
    print(
      "ERROR: pdm.lock omits dependency groups: " + ", ".join(sorted(missing_groups)),
      file=sys.stderr,
    )
    return 1

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
