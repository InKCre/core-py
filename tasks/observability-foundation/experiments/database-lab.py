"""Disposable database compatibility lab; never addresses the SVC database project."""

import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

from lab import docker, HERE, HOST

PROJECT = "inkcre-o11y-db-g1-b0a97f7c"
SOCKET = "/tmp/inkcre-o11y-db-b0a97f7c.sock"


def credentials():
  return json.loads((HERE / "runtime/database-credential.json").read_text())


def compose():
  c = credentials()
  return json.dumps(
    {
      "services": {
        "postgres": {
          "image": "pgvector/pgvector:pg17@sha256:d2ef61f42ef767baa5a1475393303cc235bcd92febd9d7014eddb48b41f3bad0",  # noqa: E501
          "cpus": 1,
          "mem_limit": "768m",
          "environment": {"POSTGRES_DB": "o11y_lab", "POSTGRES_PASSWORD": c["admin"]},
          "ports": ["127.0.0.1:35432:5432"],
          "volumes": ["data:/var/lib/postgresql/data"],
        },
        "postgrest": {
          "image": "postgrest/postgrest:v14.15@sha256:2f8e7b656f09db697a8875177694b417b35cb76c21370de07fc54e711e902326",  # noqa: E501
          "cpus": 0.25,
          "mem_limit": "256m",
          "ports": ["127.0.0.1:33000:3000"],
          "environment": {
            "PGRST_DB_URI": f"postgresql://authenticator:{c['rest']}@postgres:5432/o11y_lab",
            "PGRST_DB_SCHEMAS": "inkcre",
            "PGRST_DB_ANON_ROLE": "anonymous",
            "PGRST_DB_PRE_REQUEST": "inkcre_internal.check_jwt",
            "PGRST_JWT_AUD": "inkcre-api",
            "PGRST_JWT_SECRET": c["jwt"],
          },
        },
      },
      "volumes": {"data": {}},
    }
  )


def main(action):
  if action == "up":
    path = HERE / "runtime/database-credential.json"
    if not path.exists():
      with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "w") as f:
        json.dump(
          {key: secrets.token_urlsafe(32) for key in ["admin", "core", "rest", "jwt"]}, f
        )
    print(
      docker("compose", "-p", PROJECT, "-f", "-", "up", "-d", "postgres", data=compose())
    )
    if not Path(SOCKET).exists():
      subprocess.run(  # noqa: S603
        [
          "ssh",
          "-M",
          "-S",
          SOCKET,
          "-fNT",
          "-o",
          "BatchMode=yes",
          "-o",
          "ExitOnForwardFailure=yes",
          "-L",
          "127.0.0.1:35432:127.0.0.1:35432",
          "-L",
          "127.0.0.1:33000:127.0.0.1:33000",
          HOST,
        ],
        check=True,
      )
  elif action == "postgrest":
    print(
      docker("compose", "-p", PROJECT, "-f", "-", "up", "-d", "postgrest", data=compose())
    )
  elif action in {"stop", "remove"}:
    args = ["stop"] if action == "stop" else ["down", "--volumes"]
    print(docker("compose", "-p", PROJECT, "-f", "-", *args, data=compose()))
    if Path(SOCKET).exists():
      subprocess.run(["ssh", "-S", SOCKET, "-O", "exit", HOST], check=True)  # noqa: S603
  else:
    raise SystemExit("Use up, postgrest, stop, or remove")


if __name__ == "__main__":
  main(sys.argv[1])
