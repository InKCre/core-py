"""Query the same SDK sample and an absent/zero log discriminator from independent APIs."""

import base64
import json
from pathlib import Path
import statistics
import sys
import time
import urllib.parse
import urllib.request

HERE = Path(__file__).resolve().parent


def get(base, path, params=None):
  url = base + path + ("?" + urllib.parse.urlencode(params) if params else "")
  with urllib.request.urlopen(url, timeout=20) as response:
    return json.load(response)


def main(action):
  expected = json.loads((HERE / "runtime/expected.json").read_text())
  if action == "send-log-cases":
    now = time.time_ns()
    records = [
      {
        "timeUnixNano": str(now + i),
        "body": {"stringValue": "synthetic " + name},
        "attributes": [
          {"key": "inkcre.job.id", "value": {"intValue": "42"}},
          {"key": "inkcre.lab.case", "value": {"stringValue": name}},
          *(
            [{"key": "gen_ai.usage.input_tokens", "value": {"intValue": "0"}}]
            if name == "zero"
            else []
          ),
        ],
        "traceId": expected["execution_trace_id"],
        "spanId": expected["execution_span_id"],
      }
      for i, name in enumerate(["absent", "zero"])
    ]
    payload = {
      "resourceLogs": [
        {
          "resource": {
            "attributes": [
              {"key": "service.name", "value": {"stringValue": "inkcre-o11y-synthetic"}}
            ]
          },
          "scopeLogs": [{"logRecords": records}],
        }
      ]
    }
    request = urllib.request.Request(
      "http://127.0.0.1:34318/v1/logs",
      data=json.dumps(payload).encode(),
      headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
      assert response.status == 200
    (HERE / "runtime/stack-log-input.json").write_text(json.dumps(payload, indent=2) + "\n")
    print("Synthetic absent/zero log cases sent")
    return
  if action not in {"direct", "grafana"}:
    raise SystemExit("Use send-log-cases, direct, or grafana")
  bases = (
    {
      "loki": "http://127.0.0.1:33100",
      "prometheus": "http://127.0.0.1:39090",
      "tempo": "http://127.0.0.1:33200",
    }
    if action == "direct"
    else {
      name: "http://127.0.0.1:33001/api/datasources/proxy/uid/" + name
      for name in ["loki", "prometheus", "tempo"]
    }
  )
  log_query = {
    "query": '{service_name="inkcre-o11y-synthetic"} | inkcre_job_id="42"',
    "start": str(time.time_ns() - 3600 * 10**9),
    "limit": 100,
  }
  logs = get(bases["loki"], "/loki/api/v1/query_range", log_query)
  entries = logs["data"]["result"]
  sdk_log = next(
    row for row in entries if row["stream"].get("inkcre_lab_run_id") == expected["run_id"]
  )
  assert sdk_log["stream"]["trace_id"] == expected["execution_trace_id"]
  assert sdk_log["stream"]["span_id"] == expected["execution_span_id"]
  cases = {
    row["stream"]["inkcre_lab_case"]: row
    for row in entries
    if "inkcre_lab_case" in row["stream"]
  }
  assert "gen_ai_usage_input_tokens" not in cases["absent"]["stream"]
  assert cases["zero"]["stream"]["gen_ai_usage_input_tokens"] == "0"
  traces = {
    key: get(bases["tempo"], "/api/v2/traces/" + expected[key])
    for key in ["submission_trace_id", "execution_trace_id"]
  }
  spans = [
    span
    for resource in traces["execution_trace_id"]["trace"]["resourceSpans"]
    for scope in resource["scopeSpans"]
    for span in scope["spans"]
  ]
  executed = next(span for span in spans if span["name"] == "job.execute")
  assert (
    base64.b64decode(executed["links"][0]["traceId"]).hex()
    == expected["submission_trace_id"]
  )
  job_traces = get(
    bases["tempo"],
    "/api/search",
    {
      "q": "{ span.inkcre.job.id = 42 }",
      "start": int(time.time() - 3600),
      "end": int(time.time() + 60),
    },
  )
  assert {expected["submission_trace_id"], expected["execution_trace_id"]} <= {
    row["traceID"] for row in job_traces["traces"]
  }
  metrics = get(
    bases["prometheus"],
    "/api/v1/query",
    {"query": 'last_over_time({__name__=~"inkcre_lab.*"}[1h])'},
  )
  rows = metrics["data"]["result"]
  for name, value in {
    "inkcre_lab_jobs_total": 3,
    "inkcre_lab_duration_seconds_count": 2,
    "inkcre_lab_duration_seconds_sum": 0.4,
  }.items():
    matching = [row for row in rows if row["metric"]["__name__"] == name]
    assert len(matching) == 1 and float(matching[0]["value"][1]) == value, (name, matching)
  assert all("inkcre_job_id" not in row["metric"] for row in rows)
  buckets = {
    row["metric"]["le"]: float(row["value"][1])
    for row in rows
    if row["metric"]["__name__"] == "inkcre_lab_duration_seconds_bucket"
  }
  assert buckets == {"0.1": 1, "0.25": 1, "0.5": 2, "+Inf": 2}, buckets
  latency = []
  for _ in range(10):
    start = time.monotonic()
    get(bases["loki"], "/loki/api/v1/query_range", log_query)
    latency.append((time.monotonic() - start) * 1000)
  evidence = {
    "expected": expected,
    "logs": logs,
    "traces": traces,
    "job_trace_search": job_traces,
    "metrics": metrics,
    "log_query_roundtrip_ms": latency,
  }
  (HERE / f"runtime/stack-{action}.json").write_text(json.dumps(evidence, indent=2) + "\n")
  print(
    json.dumps(
      {
        "path": action,
        "log_to_execution_to_submission": "passed",
        "log_absent_vs_zero": "preserved; numeric metadata represented as strings",
        "cumulative_counter_and_histogram": "passed; no Job metric label",
        "small_log_query_median_ms": round(statistics.median(latency), 2),
      },
      indent=2,
    )
  )


if __name__ == "__main__":
  main(sys.argv[1])
