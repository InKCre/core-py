"""Probe -1 sentinels and explicit source-status metadata in OpenObserve 1.0.4."""

import json
from pathlib import Path
import time
import urllib.request
import uuid
from readback import query


def attrs(values):
  return [
    {
      "key": k,
      "value": {"intValue": str(v)}
      if type(v) is int
      else {"doubleValue": v}
      if type(v) is float
      else {"stringValue": v},
    }
    for k, v in values.items()
  ]


def main():
  run_id = uuid.uuid4().hex
  now = time.time_ns()
  cases = {
    "sentinel": {
      "gen_ai.usage.input_tokens": -1,
      "gen_ai.usage.output_tokens": -1,
      "gen_ai.usage.cost": -1.0,
    },
    "partial": {
      "gen_ai.usage.input_tokens": 8,
      "gen_ai.usage.output_tokens": -1,
      "gen_ai.usage.cost": -1.0,
    },
    "zero": {
      "gen_ai.usage.input_tokens": 0,
      "gen_ai.usage.output_tokens": 0,
      "gen_ai.usage.cost": 0.0,
    },
    "known": {
      "gen_ai.usage.input_tokens": 8,
      "gen_ai.usage.output_tokens": 3,
      "gen_ai.usage.cost": 0.125,
    },
    "usage_only_sentinel": {
      "gen_ai.usage.input_tokens": -1,
      "gen_ai.usage.output_tokens": -1,
    },
    "source_status": {
      "inkcre.ai.usage.input.source": "unavailable",
      "inkcre.ai.usage.output.source": "unavailable",
      "inkcre.ai.cost.source": "unavailable",
    },
  }
  spans = [
    {
      "name": name,
      "traceId": uuid.uuid4().hex,
      "spanId": uuid.uuid4().hex[:16],
      "startTimeUnixNano": str(now),
      "endTimeUnixNano": str(now + 1000),
      "attributes": attrs(
        {
          "inkcre.lab.run_id": run_id,
          "gen_ai.operation.name": "chat",
          "gen_ai.provider.name": "synthetic",
          "gen_ai.request.model": "gpt-4o",
          **values,
        }
      ),
    }
    for name, values in cases.items()
  ]
  payload = {
    "resourceSpans": [
      {
        "resource": {"attributes": attrs({"service.name": "inkcre-sentinel-probe"})},
        "scopeSpans": [{"spans": spans}],
      }
    ]
  }
  dest = Path(__file__).parent / "evidence/sentinel-saas-20261003"
  dest.mkdir(exist_ok=True)
  (dest / "sentinel-input.json").write_text(json.dumps(payload, indent=2) + "\n")
  request = urllib.request.Request(
    "http://127.0.0.1:34318/v1/traces",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
  )
  with urllib.request.urlopen(request, timeout=10) as response:
    assert response.status == 200
  sql = f"SELECT * FROM default WHERE inkcre_lab_run_id = '{run_id}'"
  deadline = time.monotonic() + 30
  while True:
    result = query(sql, "traces")
    if len({row["span_id"] for row in result["hits"]}) == len(cases):
      break
    assert time.monotonic() < deadline, "OTLP records did not become queryable"
    time.sleep(0.5)
  rows = {r["operation_name"]: r for r in result["hits"]}
  fields = [
    "gen_ai_usage_input_tokens",
    "gen_ai_usage_output_tokens",
    "gen_ai_usage_total_tokens",
    "gen_ai_usage_cost",
    "inkcre_ai_usage_input_source",
    "inkcre_ai_cost_source",
  ]
  summary = {name: {k: row.get(k) for k in fields} for name, row in rows.items()}
  assert all(
    rows["sentinel"][k] == -1
    for k in [
      "gen_ai_usage_input_tokens",
      "gen_ai_usage_output_tokens",
      "gen_ai_usage_cost",
    ]
  )
  assert rows["source_status"]["inkcre_ai_usage_input_source"] == "unavailable"
  assert (
    rows["known"]["gen_ai_usage_cost"] == 0.125
    and rows["zero"]["gen_ai_usage_input_tokens"] == 0
  )
  # OTLP retry can deliver the same span twice; isolate sentinel arithmetic from duplicates.
  unique_rows = f"SELECT DISTINCT span_id, gen_ai_usage_input_tokens, gen_ai_usage_cost FROM default WHERE inkcre_lab_run_id = '{run_id}' AND operation_name IN ('sentinel','zero','known')"  # noqa: E501
  aggregates = query(
    f"SELECT sum(gen_ai_usage_input_tokens) AS naive_input, sum(gen_ai_usage_cost) AS naive_cost, sum(CASE WHEN gen_ai_usage_input_tokens >= 0 THEN gen_ai_usage_input_tokens ELSE NULL END) AS known_input, sum(CASE WHEN gen_ai_usage_cost >= 0 THEN gen_ai_usage_cost ELSE NULL END) AS known_cost FROM ({unique_rows})",  # noqa: E501
    "traces",
  )
  assert aggregates["hits"][0] == {
    "naive_input": 7,
    "naive_cost": -0.875,
    "known_input": 8,
    "known_cost": 0.125,
  }
  report = {
    "input": payload,
    "readback": result,
    "duplicate_rows": len(result["hits"]) - len(cases),
    "summary": summary,
    "aggregate_readback": aggregates,
    "scope": "Synthetic fixed-version backend behavior only; not a production mapping or Cloud test",  # noqa: E501
  }
  (dest / "sentinel.json").write_text(json.dumps(report, indent=2) + "\n")
  print(json.dumps({"summary": summary, "aggregates": aggregates["hits"]}, indent=2))


if __name__ == "__main__":
  main()
