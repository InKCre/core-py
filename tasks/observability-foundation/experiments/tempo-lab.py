"""Task-only Tempo replacement probe, reusing the bounded Collector and SSH Docker
transport."""

import json
from pathlib import Path
import subprocess
import sys

from lab import docker, HERE, HOST, IMAGES

PROJECT = "inkcre-o11y-tempo-g1-b0a97f7c"
SOCKET = "/tmp/inkcre-o11y-tempo-b0a97f7c.sock"
IMAGE = (
  "grafana/tempo@sha256:3076b8dcdfb32fd6bc5ccef85e7b7313e6199b9cb84366257fc17ecb696db5fd"
)


def compose():
  collector = {
    "receivers": {"otlp": {"protocols": {"http": {"endpoint": "0.0.0.0:4318"}}}},
    "processors": {
      "memory_limiter": {"check_interval": "1s", "limit_mib": 384, "spike_limit_mib": 64}
    },
    "exporters": {
      "otlp_http": {
        "endpoint": "http://tempo:4318",
        "timeout": "2s",
        "retry_on_failure": {
          "initial_interval": "1s",
          "max_interval": "2s",
          "max_elapsed_time": "10s",
        },
        "sending_queue": {"sizer": "bytes", "queue_size": 1048576, "num_consumers": 1},
      }
    },
    "service": {
      "pipelines": {
        "traces": {
          "receivers": ["otlp"],
          "processors": ["memory_limiter"],
          "exporters": ["otlp_http"],
        }
      }
    },
  }
  return json.dumps(
    {
      "services": {
        "tempo": {
          "image": IMAGE,
          "cpus": 1.5,
          "mem_limit": "3584m",
          "ports": ["127.0.0.1:33200:3200"],
          "command": ["-target=all", "-config.file=/etc/tempo/lab.yaml"],
          "volumes": ["data:/var/tempo"],
          "configs": [{"source": "tempo", "target": "/etc/tempo/lab.yaml"}],
        },
        "collector": {
          "image": IMAGES["collector"],
          "cpus": 0.5,
          "mem_limit": "512m",
          "ports": ["127.0.0.1:34318:4318"],
          "command": ["--config=/etc/otelcol/lab.yaml"],
          "configs": [{"source": "collector", "target": "/etc/otelcol/lab.yaml"}],
        },
      },
      "configs": {
        "tempo": {"content": (HERE / "tempo.yaml").read_text()},
        "collector": {"content": json.dumps(collector)},
      },
      "volumes": {"data": {}},
    }
  )


def main(action):
  if action == "up":
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
          "127.0.0.1:33200:127.0.0.1:33200",
          "-L",
          "127.0.0.1:34318:127.0.0.1:34318",
          HOST,
        ],
        check=True,
      )
  elif action == "restart":
    print(docker("restart", PROJECT + "-tempo-1"))
  elif action in {"stop", "remove"}:
    args = ["stop"] if action == "stop" else ["down", "--volumes"]
    print(docker("compose", "-p", PROJECT, "-f", "-", *args, data=compose()))
    if Path(SOCKET).exists():
      subprocess.run(["ssh", "-S", SOCKET, "-O", "exit", HOST], check=True)  # noqa: S603
  elif action == "logs":
    print(
      docker("compose", "-p", PROJECT, "-f", "-", "logs", "--tail", "35", data=compose())
    )
  elif action == "stats":
    print(
      docker(
        "stats",
        "--no-stream",
        "--format",
        "{{json .}}",
        PROJECT + "-tempo-1",
        PROJECT + "-collector-1",
      )
    )
  else:
    raise SystemExit("Use up, restart, stop, remove, logs, or stats")


if __name__ == "__main__":
  main(sys.argv[1])
