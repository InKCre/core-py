"""Enforce an append-only migration baseline across legacy branch divergence."""

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VERSIONS_DIRECTORY = PROJECT_ROOT / "migrations" / "versions"
MANIFEST_PATH = Path("migrations/revision-integrity.json")
MANIFEST_FILE = PROJECT_ROOT / MANIFEST_PATH
MANIFEST_FORMAT = 1


def _load_manifest(content: str, source: str) -> dict[str, str]:
  try:
    document: Any = json.loads(content)
    revision_hashes = document["revisions"]
  except (json.JSONDecodeError, KeyError, TypeError) as error:
    raise ValueError(f"{source} is not a valid revision manifest") from error

  if document.get("format") != MANIFEST_FORMAT or not isinstance(
    revision_hashes,
    dict,
  ):
    raise ValueError(f"{source} has an unsupported revision manifest format")

  if not all(
    isinstance(name, str)
    and Path(name).name == name
    and name.endswith(".py")
    and isinstance(digest, str)
    and len(digest) == 64
    for name, digest in revision_hashes.items()
  ):
    raise ValueError(f"{source} contains an invalid revision entry")

  return revision_hashes


def _worktree_manifest() -> dict[str, str]:
  return _load_manifest(MANIFEST_FILE.read_text(), str(MANIFEST_PATH))


def _revision_files() -> dict[str, Path]:
  return {
    path.name: path for path in VERSIONS_DIRECTORY.glob("*.py") if path.is_file()
  }


def _protected_revision_violations(
  expected: dict[str, str],
  revision_files: dict[str, Path],
) -> list[str]:
  violations: list[str] = []

  missing = set(expected) - set(revision_files)
  violations.extend(f"missing revision: {name}" for name in sorted(missing))

  for name, expected_digest in sorted(expected.items()):
    revision = revision_files.get(name)
    if revision is None:
      continue
    actual_digest = sha256(revision.read_bytes()).hexdigest()
    if actual_digest != expected_digest:
      violations.append(f"modified revision: {name}")

  return violations


def validate_worktree_manifest() -> list[str]:
  """Return integrity violations for the checked-out revision files."""
  expected = _worktree_manifest()
  revision_files = _revision_files()
  violations = _protected_revision_violations(expected, revision_files)
  unrecorded = set(revision_files) - set(expected)
  violations.extend(f"unrecorded revision: {name}" for name in sorted(unrecorded))
  return violations


def record_new_revisions() -> int:
  """Append new revision digests without changing the protected baseline."""
  current = _worktree_manifest()
  revision_files = _revision_files()
  violations = _protected_revision_violations(current, revision_files)
  if violations:
    print(
      "ERROR: refusing to record while protected revisions have changed:",
      file=sys.stderr,
    )
    for violation in violations:
      print(f"  {violation}", file=sys.stderr)
    return 1

  new_names = sorted(set(revision_files) - set(current))
  if not new_names:
    print("No new migration revisions to record")
    return 0

  updated = dict(current)
  for name in new_names:
    updated[name] = sha256(revision_files[name].read_bytes()).hexdigest()

  document = {"format": MANIFEST_FORMAT, "revisions": dict(sorted(updated.items()))}
  MANIFEST_FILE.write_text(f"{json.dumps(document, indent=2)}\n")
  print(f"Recorded {len(new_names)} new migration revision(s):")
  for name in new_names:
    print(f"  {name}")
  return 0


def _base_manifest(base_ref: str) -> dict[str, str] | None:
  if base_ref and set(base_ref) == {"0"}:
    return None

  ref_check = subprocess.run(  # noqa: S603
    ["git", "rev-parse", "--verify", f"{base_ref}^{{commit}}"],
    cwd=PROJECT_ROOT,
    check=False,
    capture_output=True,
    text=True,
  )
  if ref_check.returncode != 0:
    raise ValueError(f"cannot resolve Git base ref {base_ref!r}")

  result = subprocess.run(  # noqa: S603
    ["git", "show", f"{base_ref}:{MANIFEST_PATH.as_posix()}"],
    cwd=PROJECT_ROOT,
    check=False,
    capture_output=True,
    text=True,
  )
  if result.returncode != 0:
    return None
  return _load_manifest(result.stdout, f"{base_ref}:{MANIFEST_PATH}")


def main() -> int:
  """Validate the worktree and preserve every manifest entry from the base."""
  if sys.argv[1:] == ["--record-new"]:
    return record_new_revisions()

  if len(sys.argv) > 2:
    print(
      "usage: python scripts/check_migration_history.py "
      "[--record-new | base-ref]",
      file=sys.stderr,
    )
    return 2

  try:
    current = _worktree_manifest()
    violations = validate_worktree_manifest()
    base_ref = sys.argv[1] if len(sys.argv) == 2 else None
    base = _base_manifest(base_ref) if base_ref is not None else None
  except (OSError, ValueError) as error:
    print(f"ERROR: {error}", file=sys.stderr)
    return 1

  if base is not None:
    for name, digest in sorted(base.items()):
      if current.get(name) != digest:
        violations.append(f"changed protected manifest entry: {name}")

  if violations:
    print("ERROR: migration history integrity failed:", file=sys.stderr)
    for violation in violations:
      print(f"  {violation}", file=sys.stderr)
    return 1

  if base_ref is not None and base is None:
    print(
      f"Migration integrity baseline bootstrapped; {base_ref} has no manifest"
    )
  elif base_ref is not None:
    print(f"Migration history is append-only relative to {base_ref}")
  else:
    print("Migration revision integrity manifest is current")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
