"""Verify that the tracked requirements export matches the PDM lock."""

from difflib import unified_diff
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from _tooling import run_pdm


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"


def main() -> int:
  """Export into a temporary file and compare without mutating the worktree."""
  with TemporaryDirectory(prefix="inkcre-requirements-") as temporary_directory:
    exported_file = Path(temporary_directory) / "requirements.txt"
    result = run_pdm(
      ["export", "--prod", "--output", str(exported_file)],
      cwd=PROJECT_ROOT,
    )

    if result is None:
      print("ERROR: PDM is unavailable", file=sys.stderr)
      return 1
    if result.returncode != 0:
      print("ERROR: requirements export failed", file=sys.stderr)
      if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
      return result.returncode

    tracked = REQUIREMENTS_FILE.read_text().splitlines(keepends=True)
    exported = exported_file.read_text().splitlines(keepends=True)

  if tracked == exported:
    print("requirements.txt matches the production PDM lock export")
    return 0

  print(
    "ERROR: requirements.txt is stale; run "
    "`pdm export --prod --output requirements.txt`",
    file=sys.stderr,
  )
  sys.stderr.writelines(
    unified_diff(
      tracked,
      exported,
      fromfile="requirements.txt",
      tofile="PDM production export",
    )
  )
  return 1


if __name__ == "__main__":
  raise SystemExit(main())
