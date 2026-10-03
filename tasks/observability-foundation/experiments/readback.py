"""Independently query OpenObserve; exporter success is not this check's oracle."""

import base64
import json
from pathlib import Path
import statistics
import time
import urllib.request

from lab import credentials

HERE = Path(__file__).resolve().parent


def query(sql, kind):
  cred = credentials()
  auth = base64.b64encode(f"{cred['email']}:{cred['password']}".encode()).decode()
  body = {
    "query": {
      "sql": sql,
      "start_time": int((time.time() - 86400) * 1e6),
      "end_time": int((time.time() + 60) * 1e6),
      "size": 100,
    }
  }
  request = urllib.request.Request(
    "http://127.0.0.1:35080/api/default/_search?type=" + kind,
    data=json.dumps(body).encode(),
    headers={"Authorization": "Basic " + auth, "Content-Type": "application/json"},
  )
  with urllib.request.urlopen(request, timeout=20) as response:
    result = json.load(response)
  assert not result.get("is_partial"), result
  return result


def main():
  expected = json.loads((HERE / "runtime/expected.json").read_text())
  run_id = expected["run_id"]
  assert len(run_id) == 32 and all(c in "0123456789abcdef" for c in run_id)
  sql = f"SELECT * FROM default WHERE inkcre_lab_run_id = '{run_id}'"
  traces = query(sql, "traces")
  logs = query(sql, "logs")
  spans = {row["operation_name"]: row for row in traces["hits"]}
  assert len(spans) == 3
  executed = spans["job.execute"]
  assert executed["trace_id"] == expected["execution_trace_id"]
  assert executed.get("reference_parent_span_id") in (None, "")
  assert (
    spans["chat synthetic-model"]["reference_parent_span_id"]
    == expected["execution_span_id"]
  )
  link = json.loads(executed["links"])[0]["context"]
  assert link["traceId"] == expected["submission_trace_id"]
  assert link["spanId"] == expected["submission_span_id"]
  assert executed["trace_id"] != link["traceId"]
  assert (
    executed["inkcre_job_id"] == "42"
  )  # Observed backend projection, not OTLP's original type.
  assert len(logs["hits"]) == 1
  assert logs["hits"][0]["trace_id"] == expected["execution_trace_id"]
  assert logs["hits"][0]["span_id"] == expected["execution_span_id"]
  assert logs["hits"][0]["inkcre_job_id"] == 42
  ai = spans["chat synthetic-model"]
  assert ai["gen_ai_usage_input_tokens"] == 8
  assert ai["gen_ai_usage_output_tokens"] == 3
  metric_data = {}
  # Cumulative points are snapshots. Summing repeated exports would double-count them.
  for name, value in {
    "inkcre_lab_jobs": 3,
    "inkcre_lab_duration_count": 2,
    "inkcre_lab_duration_sum": 0.4,
  }.items():
    result = query(f"SELECT * FROM {name} ORDER BY _timestamp DESC LIMIT 1", "metrics")
    assert result["hits"][0]["value"] == value, result
    metric_data[name] = result
  buckets = query("SELECT * FROM inkcre_lab_duration_bucket", "metrics")
  assert {r["le"]: r["value"] for r in buckets["hits"]} == {
    "0.1": 1,
    "0.25": 1,
    "0.5": 2,
    "inf": 2,
  }
  latency = []
  for _ in range(20):
    started = time.perf_counter()
    assert len(query(sql, "traces")["hits"]) == 3
    latency.append((time.perf_counter() - started) * 1000)
  evidence = {
    "expected": expected,
    "traces": traces,
    "logs": logs,
    "metrics": metric_data,
    "buckets": buckets,
    "query_roundtrip_ms": latency,
  }
  (HERE / "runtime/readback.json").write_text(json.dumps(evidence, indent=2) + "\n")
  print(
    json.dumps(
      {
        "three_signals_and_links": "passed",
        "small_warm_query_n": 20,
        "small_warm_query_p95_ms": sorted(latency)[18],
        "small_warm_query_median_ms": statistics.median(latency),
        "backend_added_cost_without_input": ai.get("gen_ai_usage_cost"),
        "backend_added_agent_version_without_input": ai.get("gen_ai_agent_version"),
        "trace_job_attribute_type": type(executed["inkcre_job_id"]).__name__,
      },
      indent=2,
    )
  )


if __name__ == "__main__":
  main()
