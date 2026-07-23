"""Read-only checks for the repository's foundation toolchain."""

from pathlib import Path
import re
import sys

from _tooling import run_command, run_pdm


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PYTHON = (3, 12)
EXPECTED_PDM = "2.27.0"
REQUIRED_FILES = (
  "pdm.lock",
  "pyproject.toml",
  "alembic.ini",
  "Procfile",
)
REQUIRED_TOOLS = ("alembic", "pyrefly", "pytest", "ruff")


def _pdm_version() -> str | None:
  result = run_pdm(["--version"], cwd=PROJECT_ROOT)
  if result is None or result.returncode != 0:
    return None
  match = re.search(r"\b(\d+\.\d+\.\d+)\b", result.stdout)
  return match.group(1) if match else None


def main() -> int:
  """Return non-zero when the foundation toolchain is inconsistent."""
  errors: list[str] = []

  if sys.version_info[:2] != EXPECTED_PYTHON:
    errors.append(
      f"Python {EXPECTED_PYTHON[0]}.{EXPECTED_PYTHON[1]} is required; "
      f"found {sys.version_info.major}.{sys.version_info.minor}"
    )

  python_version_path = PROJECT_ROOT / ".python-version"
  if not python_version_path.is_file():
    errors.append("required file is missing: .python-version")
  else:
    python_version = python_version_path.read_text().strip()
    if python_version != "3.12":
      errors.append(f".python-version must contain 3.12; found {python_version!r}")

  pdm_version = _pdm_version()
  if pdm_version != EXPECTED_PDM:
    errors.append(f"PDM {EXPECTED_PDM} is required; found {pdm_version or 'unavailable'}")

  for relative_path in REQUIRED_FILES:
    if not (PROJECT_ROOT / relative_path).is_file():
      errors.append(f"required file is missing: {relative_path}")

  for tool in REQUIRED_TOOLS:
    result = run_command(tool, ["--version"], cwd=PROJECT_ROOT)
    if result is None or result.returncode != 0:
      errors.append(f"required project tool is unavailable: {tool}")

  if errors:
    for error in errors:
      print(f"ERROR: {error}", file=sys.stderr)
    return 1

  print(
    "Foundation toolchain ready: "
    f"Python {sys.version_info.major}.{sys.version_info.minor}, PDM {pdm_version}"
  )
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
