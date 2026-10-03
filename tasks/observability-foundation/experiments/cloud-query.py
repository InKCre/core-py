"""Read synthetic OTLP acceptance data through a Viewer Grafana service account."""

import base64
from datetime import datetime
import json
from pathlib import Path
import re
import time

from dotenv import dotenv_values
import httpx

HERE = Path(__file__).resolve().parent
config = dotenv_values(HERE.parents[2] / ".env")
probe = json.loads((HERE / "evidence/cloud-probe.json").read_text())
report = {"run_id": probe["run_id"], "signals": {}}


def canonical_id(value):
  if re.fullmatch(r"[0-9a-f]{16}|[0-9a-f]{32}", value):
    return value
  return base64.b64decode(value).hex()


def spans_in(value):
  if isinstance(value, dict):
    if "spanId" in value and "name" in value:
      yield value
    for child in value.values():
      yield from spans_in(child)
  elif isinstance(value, list):
    for child in value:
      yield from spans_in(child)


def instances_in(value):
  if isinstance(value, dict):
    fields = attributes(value)
    if fields.get("inkcre.deployment.id") == probe["run_id"]:
      if fields.get("service.instance.id"):
        yield fields["service.instance.id"]
    for child in value.values():
      yield from instances_in(child)
  elif isinstance(value, list):
    for child in value:
      yield from instances_in(child)


def attributes(value):
  return {
    item["key"]: next(iter(item["value"].values())) for item in value.get("attributes", [])
  }


with httpx.Client(
  base_url=config["GRAFANA_URL"].rstrip("/"),
  headers={"Authorization": "Bearer " + config["GRAFANA_SERVICE_ACCOUNT_TOKEN"]},
  timeout=20,
  follow_redirects=False,
) as client:
  catalog_response = client.get("/api/datasources")
  assert catalog_response.status_code == 200, "Viewer datasource discovery failed"
  catalog = catalog_response.json()
  datasources = {}
  for signal, kind, suffix in (
    ("traces", "tempo", "-traces"),
    ("logs", "loki", "-logs"),
    ("metrics", "prometheus", "-prom"),
  ):
    matches = [
      item for item in catalog if item["type"] == kind and item["name"].endswith(suffix)
    ]
    assert len(matches) == 1, "Choose the intended datasource before querying"
    datasources[signal] = "/api/datasources/proxy/uid/" + matches[0]["uid"]

  traces = []
  instance_ids = set()
  for key in ("submit_trace_id", "execute_trace_id"):
    response = client.get(
      datasources["traces"] + "/api/traces/" + probe[key],
      headers={"Accept": "application/json"},
    )
    report["signals"][key] = {"status": response.status_code}
    if response.status_code == 200:
      traces.extend(spans_in(response.json()))
      instance_ids.update(instances_in(response.json()))
  submission = next((span for span in traces if span["name"] == "job.submit"), None)
  execution = next((span for span in traces if span["name"] == "job.execute"), None)
  chat = next((span for span in traces if span["name"] == "ai.chat"), None)
  trace_ok = False
  if submission and execution and chat:
    trace_ok = (
      canonical_id(submission["traceId"]) == probe["submit_trace_id"]
      and canonical_id(execution["traceId"]) == probe["execute_trace_id"]
      and canonical_id(chat["parentSpanId"]) == canonical_id(execution["spanId"])
      and any(
        canonical_id(link["traceId"]) == probe["submit_trace_id"]
        and canonical_id(link["spanId"]) == canonical_id(submission["spanId"])
        for link in execution.get("links", [])
      )
      and attributes(chat).get("inkcre.ai.usage.input.source") == "provider"
      and int(attributes(chat).get("gen_ai.usage.input_tokens", -1)) == 0
      and attributes(chat).get("inkcre.ai.usage.output.source") == "unavailable"
      and "gen_ai.usage.output_tokens" not in attributes(chat)
    )
  report["signals"]["traces"] = {"verified": trace_ok, "span_count": len(traces)}
  start = int(datetime.fromisoformat(probe["started_at"]).timestamp()) - 5
  response = client.get(
    datasources["logs"] + "/loki/api/v1/query_range",
    params={
      "query": '{service_name="core-py"} | inkcre_deployment_id="' + probe["run_id"] + '"',
      "start": str(start * 10**9),
      "end": str(int(time.time() * 10**9)),
      "limit": "10",
    },
  )
  logs = (
    response.json().get("data", {}).get("result", []) if response.status_code == 200 else []
  )
  events = [value[1] for stream in logs for value in stream.get("values", [])]
  report["signals"]["logs"] = {
    "status": response.status_code,
    "verified": {"job.submitted", "job.closed"}.issubset(events),
    "events": events,
  }
  assert len(instance_ids) == 1, "Synthetic Resource identity did not survive trace storage"
  instance_id = next(iter(instance_ids))
  selector = (
    '{__name__=~"inkcre_operation_count_total|inkcre_ai_token_usage_total|'
    'inkcre_ai_usage_missing_total|inkcre_operation_duration_seconds_count",'
    'service_instance_id="' + instance_id + '"}'
  )
  response = client.get(
    datasources["metrics"] + "/api/v1/query",
    params={"query": selector, "time": str(start + 35)},
  )
  series = (
    response.json().get("data", {}).get("result", []) if response.status_code == 200 else []
  )

  def sample(name, **labels):
    matches = [
      float(item["value"][1])
      for item in series
      if item["metric"].get("__name__") == name
      and all(item["metric"].get(key) == value for key, value in labels.items())
    ]
    return matches

  metrics_ok = all(
    sample("inkcre_operation_count_total", operation=name, outcome="success") == [1]
    and sample("inkcre_operation_duration_seconds_count", operation=name, outcome="success")
    == [1]
    for name in ("ai.chat", "job.submit", "job.execute")
  ) and (
    sample("inkcre_ai_token_usage_total", token_type="input") == [0]
    and sample("inkcre_ai_token_usage_total", token_type="output") == []
    and sample("inkcre_ai_usage_missing_total", token_type="output") == [1]
  )
  report["signals"]["metrics"] = {
    "status": response.status_code,
    "series": series,
    "verified": metrics_ok,
  }
report["query_verified"] = all(
  report["signals"][key]["verified"] for key in ("traces", "logs", "metrics")
)
(HERE / "evidence/cloud-query.json").write_text(json.dumps(report, indent=2) + "\n")
print(
  json.dumps(
    {
      "run_id": report["run_id"],
      "query_verified": report["query_verified"],
      "signals": {
        key: {k: v for k, v in value.items() if k != "series"}
        for key, value in report["signals"].items()
      },
    },
    indent=2,
  )
)
assert report["query_verified"], "Cloud readback did not match the synthetic source"
