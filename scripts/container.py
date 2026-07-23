"""Provider-neutral process contract for the OCI artifact."""

import os
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def _web() -> int:
  port = os.getenv("PORT", "8000")
  if not port.isdigit():
    raise SystemExit("PORT must be an integer")

  os.execvp(
    "uvicorn",
    [
      "uvicorn",
      "run:api_app",
      "--host",
      "0.0.0.0",
      "--port",
      port,
    ],
  )
  return 0


def _migrate() -> int:
  os.execvp("alembic", ["alembic", "upgrade", "head"])
  return 0


def _ready() -> int:
  from app.health import check_database_readiness

  result = check_database_readiness()
  print(result.reason)
  return 0 if result.ready else 1


COMMANDS = {
  "web": _web,
  "migrate": _migrate,
  "ready": _ready,
}


def main(argv: list[str] | None = None) -> int:
  args = argv if argv is not None else sys.argv[1:]
  if len(args) != 1 or args[0] not in COMMANDS:
    available = ", ".join(sorted(COMMANDS))
    print(f"usage: container.py <{available}>", file=sys.stderr)
    return 2
  return COMMANDS[args[0]]()


if __name__ == "__main__":
  raise SystemExit(main())
