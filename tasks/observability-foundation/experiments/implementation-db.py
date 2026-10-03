"""Run source lifecycle commands only against this task's disposable database."""

import json
import os
from pathlib import Path
import subprocess
import sys

import psycopg
from psycopg import sql

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CREDENTIALS = json.loads((HERE / "runtime/database-credential.json").read_text())
DB = "o11y_impl"
ADMIN = f"postgresql://postgres:{CREDENTIALS['admin']}@127.0.0.1:35432/{DB}"
CORE = f"postgresql+psycopg://inkcre_core:{CREDENTIALS['core']}@127.0.0.1:35432/{DB}"


def environment():
  return {
    **os.environ,
    "INKCRE_ENV_FILE": "",
    "DATABASE_URL": CORE,
    "MIGRATION_DATABASE_URL": ADMIN,
    "JWT_SECRET": CREDENTIALS["jwt"],
    "CORE_DATABASE_PASSWORD": CREDENTIALS["core"],
    "POSTGREST_DATABASE_PASSWORD": CREDENTIALS["rest"],
  }


def main():
  if sys.argv[1:] == ["create"]:
    with psycopg.connect(ADMIN.rsplit("/", 1)[0] + "/postgres", autocommit=True) as conn:
      if not conn.execute("SELECT 1 FROM pg_database WHERE datname=%s", (DB,)).fetchone():
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB)))
    print("Disposable implementation database is available; old synthetic data retained.")
    return
  result = subprocess.run(  # noqa: S603
    sys.argv[1:], cwd=ROOT, env=environment(), capture_output=True, text=True, check=False
  )
  output = result.stdout + result.stderr
  (HERE / "runtime/implementation-db-last.log").write_text(output)
  for value in CREDENTIALS.values():
    output = output.replace(value, "<lab-secret>")
  print(output, end="")
  raise SystemExit(result.returncode)


if __name__ == "__main__":
  main()
