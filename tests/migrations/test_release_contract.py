from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_release_only_applies_checked_in_migrations():
  release_commands = [
    line.removeprefix("release:").strip()
    for line in (PROJECT_ROOT / "Procfile").read_text().splitlines()
    if line.startswith("release:")
  ]

  assert release_commands == ["alembic upgrade head"]
