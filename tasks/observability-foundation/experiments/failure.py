"""Bounded backend outage probe. This does not run an InKCre business operation."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import time
import urllib.request
import uuid

from lab import docker, PROJECT

HERE = Path(__file__).resolve().parent


def metrics():
  with urllib.request.urlopen("http://127.0.0.1:38888/metrics", timeout=5) as response:
    return response.read().decode()


def send(index):
  now = time.time_ns()
  spans = [
    {
      "name": "fault.probe",
      "traceId": uuid.uuid4().hex,
      "spanId": uuid.uuid4().hex[:16],
      "startTimeUnixNano": str(now),
      "endTimeUnixNano": str(now + 1000000),
      "attributes": [
        {"key": "inkcre.lab.padding", "value": {"stringValue": "synthetic-" * 228}}
      ],
    }
    for _ in range(256)
  ]
  data = {
    "resourceSpans": [
      {
        "resource": {
          "attributes": [
            {"key": "service.name", "value": {"stringValue": "inkcre-o11y-outage"}}
          ]
        },
        "scopeSpans": [{"spans": spans}],
      }
    ]
  }
  request = urllib.request.Request(
    "http://127.0.0.1:34318/v1/traces",
    data=json.dumps(data).encode(),
    headers={"Content-Type": "application/json"},
  )
  with urllib.request.urlopen(request, timeout=10) as response:
    return {"request": index, "status": response.status, "body": response.read().decode()}


def main():
  before = metrics()
  responses = []
  samples = []
  docker("stop", PROJECT + "-openobserve-1")
  try:
    with ThreadPoolExecutor(max_workers=4) as pool:
      responses = list(pool.map(send, range(16)))
    for _ in range(15):
      samples.append(metrics())
      time.sleep(1)
    stats = docker(
      "stats", "--no-stream", "--format", "{{json .}}", PROJECT + "-collector-1"
    )
  finally:
    docker("start", PROJECT + "-openobserve-1")
  after = metrics()
  evidence = {
    "submitted_spans": 4096,
    "before": before,
    "samples": samples,
    "after": after,
    "responses": responses,
    "collector_stats_after_burst": stats,
  }
  (HERE / "runtime/failure.json").write_text(json.dumps(evidence, indent=2) + "\n")
  interesting = [
    line
    for line in after.splitlines()
    if not line.startswith("#")
    and any(
      key in line
      for key in [
        "enqueue_failed_spans",
        "send_failed_spans",
        "queue_size",
        "queue_capacity",
        "process_memory_rss",
      ]
    )
  ]
  assert any(
    "enqueue_failed_spans" in line and float(line.rsplit(" ", 1)[1]) > 0
    for line in interesting
  ), "Outage did not exercise queue overflow"
  print(
    json.dumps(
      {
        "http_200_responses": sum(r["status"] == 200 for r in responses),
        "submitted_spans": 4096,
        "observed": interesting,
        "business_failure_isolation": "not exercised",
      },
      indent=2,
    )
  )


if __name__ == "__main__":
  main()
