"""Task-only isolated Docker recipe; python3 lab.py up|stop|stats|logs|backend-
stop|backend-start.

Uses the already-authorized SSH Docker host, never the SVC database project.
Stop preserves synthetic data for repeatable inspection; removal is a separate explicit
command.
"""

import base64
import json
import os
from pathlib import Path
import secrets
import shlex
import subprocess
import sys


HERE = Path(__file__).resolve().parent
RUNTIME = HERE / "runtime"
PROJECT = "inkcre-o11y-g1-b0a97f7c"
HOST = "wsl.win-ws.localhost"
DOCKER = "/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe"
SOCKET = "/tmp/inkcre-o11y-g1-b0a97f7c.sock"
IMAGES = {
  "openobserve": "openobserve/openobserve@sha256:d4a878fac1f6c56003764f7f2a1625668917388f167e222c8c810de3f54c56ba",  # noqa: E501
  "collector": "otel/opentelemetry-collector@sha256:310a800ad69ee430e7c541796852a242c9c7db97aaad4daa5ccf843c525fbdb2",  # noqa: E501
}


def docker(*args, data=None):
  command = [DOCKER, *args]
  if os.getenv("LAB_WSL_INTEROP"):
    command = ["env", "WSL_INTEROP=" + os.environ["LAB_WSL_INTEROP"], *command]
  return subprocess.check_output(  # noqa: S603
    ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", HOST, shlex.join(command)],
    input=data,
    text=True,
    timeout=60,
  )


def credentials():
  return json.loads((RUNTIME / "credential.json").read_text())


def compose():
  cred = credentials()
  auth = base64.b64encode(f"{cred['email']}:{cred['password']}".encode()).decode()
  return json.dumps(
    {
      "services": {
        "openobserve": {
          "image": IMAGES["openobserve"],
          "cpus": 1.5,
          "mem_limit": "3584m",
          "ports": ["127.0.0.1:35080:5080"],
          "environment": {
            "ZO_ROOT_USER_EMAIL": cred["email"],
            "ZO_ROOT_USER_PASSWORD": cred["password"],
            "ZO_DATA_DIR": "/data",
            "ZO_LOCAL_MODE": "true",
            "ZO_TELEMETRY": "false",
            "ZO_PROMETHEUS_ENABLED": "true",
            "ZO_DISK_CACHE_MAX_SIZE": "256",
          },
          "volumes": ["data:/data"],
        },
        "collector": {
          "image": IMAGES["collector"],
          "cpus": 0.5,
          "mem_limit": "512m",
          "ports": ["127.0.0.1:34318:4318", "127.0.0.1:38888:8888"],
          "command": ["--config=/etc/otelcol/lab.yaml"],
          "environment": {"LAB_AUTH": auth},
          "configs": [{"source": "collector", "target": "/etc/otelcol/lab.yaml"}],
        },
      },
      # Compose expands dollar signs; the Collector owns this env expansion.
      "configs": {
        "collector": {"content": (HERE / "collector.yaml").read_text().replace("$", "$$")}
      },
      "volumes": {"data": {}},
      "networks": {"default": {}},
    }
  )


def main(action):
  if action == "up":
    RUNTIME.mkdir(exist_ok=True, mode=0o700)
    credential = RUNTIME / "credential.json"
    if not credential.exists():
      with os.fdopen(
        os.open(credential, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w"
      ) as file:
        json.dump(
          {"email": "lab@example.invalid", "password": secrets.token_urlsafe(32)}, file
        )
    print(docker("compose", "-p", PROJECT, "-f", "-", "up", "-d", data=compose()))
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
          "127.0.0.1:35080:127.0.0.1:35080",
          "-L",
          "127.0.0.1:34318:127.0.0.1:34318",
          "-L",
          "127.0.0.1:38888:127.0.0.1:38888",
          HOST,
        ],
        check=True,
      )
  elif action in {"stop", "remove"}:
    command = ["stop"] if action == "stop" else ["down", "--volumes"]
    print(docker("compose", "-p", PROJECT, "-f", "-", *command, data=compose()))
    if Path(SOCKET).exists():
      subprocess.run(["ssh", "-S", SOCKET, "-O", "exit", HOST], check=True)  # noqa: S603
  elif action == "stats":
    print(
      docker(
        "stats",
        "--no-stream",
        "--format",
        "{{json .}}",
        f"{PROJECT}-openobserve-1",
        f"{PROJECT}-collector-1",
      )
    )
  elif action == "logs":
    print(
      docker("compose", "-p", PROJECT, "-f", "-", "logs", "--tail", "40", data=compose())
    )
  elif action in {"backend-stop", "backend-start"}:
    print(docker(action.removeprefix("backend-"), f"{PROJECT}-openobserve-1"))
  else:
    raise SystemExit("Use up, stop, remove, stats, logs, backend-stop, or backend-start")


if __name__ == "__main__":
  main(sys.argv[1])
