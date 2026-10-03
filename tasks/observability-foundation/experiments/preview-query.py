"""Independently read bounded preview Job evidence from Grafana datasource APIs."""

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
source = json.loads((HERE / "evidence/preview-browser-on.json").read_text())
deployment = json.loads((HERE / "runtime/preview-restore.json").read_text())["run_id"]
job = source["business"]
traceparent = job["submissionTraceparent"].split("-")
start = (
  int(datetime.fromisoformat(source["startedAt"].replace("Z", "+00:00")).timestamp()) - 10
)
end = int(time.time())
report = {
  "deployment_id": deployment,
  "job_id": job["id"],
  "source": source["clientSource"],
  "signals": {},
}


def ident(value):
  return (
    value
    if re.fullmatch(r"[0-9a-f]{16}|[0-9a-f]{32}", value)
    else base64.b64decode(value).hex()
  )


def attrs(value):
  return {
    item["key"]: next(iter(item["value"].values())) for item in value.get("attributes", [])
  }


def walk(value):
  if isinstance(value, dict):
    yield value
    for child in value.values():
      yield from walk(child)
  elif isinstance(value, list):
    for child in value:
      yield from walk(child)


with httpx.Client(
  base_url=config["GRAFANA_URL"],
  headers={"Authorization": "Bearer " + config["GRAFANA_SERVICE_ACCOUNT_TOKEN"]},
  timeout=30,
) as client:

  def get(path, **kwargs):
    r = client.get(path, **kwargs)
    if r.status_code != 200:
      raise RuntimeError(f"Grafana status {r.status_code}, path {path}")
    return r.json()

  catalog = get("/api/datasources")
  ds = {
    kind: "/api/datasources/proxy/uid/"
    + next(x["uid"] for x in catalog if x["type"] == kind and x["name"].endswith(suffix))
    for kind, suffix in [("tempo", "-traces"), ("loki", "-logs"), ("prometheus", "-prom")]
  }
  search = get(
    ds["tempo"] + "/api/search",
    params={
      "q": (
        f'{{ resource.inkcre.deployment.id = "{deployment}" '
        f"&& span.inkcre.job.id = {job['id']} }}"
      ),
      "start": start,
      "end": end,
      "limit": 20,
    },
  )
  ids = {traceparent[1]} | {x["traceID"] for x in search.get("traces", [])}
  spans = []
  resources = []
  for trace_id in sorted(ids):
    r = client.get(
      ds["tempo"] + "/api/traces/" + trace_id, headers={"Accept": "application/json"}
    )
    if r.status_code != 200:
      continue
    for item in walk(r.json()):
      if "spanId" in item and "name" in item:
        spans.append(item)
      if "service.instance.id" in attrs(item):
        resources.append(attrs(item))
  submission = next(
    (
      s for s in spans if s["name"] == "job.submit" and ident(s["spanId"]) == traceparent[2]
    ),
    None,
  )
  execution = next(
    (
      s
      for s in spans
      if s["name"] == "job.execute" and int(attrs(s).get("inkcre.job.id", -1)) == job["id"]
    ),
    None,
  )
  trace_ok = bool(
    submission
    and execution
    and ident(execution["traceId"]) != traceparent[1]
    and any(
      ident(link["traceId"]) == traceparent[1] and ident(link["spanId"]) == traceparent[2]
      for link in execution.get("links", [])
    )
  )
  report["signals"]["traces"] = {
    "verified": trace_ok,
    "submit_trace_id": traceparent[1],
    "execution_trace_id": ident(execution["traceId"]) if execution else None,
    "span_count": len(spans),
    "services": sorted({r.get("service.name", "") for r in resources}),
  }
  logs = get(
    ds["loki"] + "/loki/api/v1/query_range",
    params={
      "query": (
        '{service_name=~"core-py|inkcre.client-web"} '
        f'| inkcre_deployment_id="{deployment}" | inkcre_job_id="{job["id"]}"'
      ),
      "start": str(start * 10**9),
      "end": str(end * 10**9),
      "limit": 50,
    },
  )
  events = [
    v[1]
    for stream in logs.get("data", {}).get("result", [])
    for v in stream.get("values", [])
  ]
  report["signals"]["logs"] = {
    "verified": {"job.submitted", "job.started", "job.closed"}.issubset(events),
    "events": events,
  }
  metric_rows = []
  for resource in resources:
    result = get(
      ds["prometheus"] + "/api/v1/query",
      params={
        "query": (
          '{__name__=~"inkcre_operation_duration_seconds_count|'
          'inkcre_operation_count_total",service_instance_id="'
        )
        + resource["service.instance.id"]
        + '"}',
        "time": min(
          end,
          int(
            datetime.fromisoformat(source["finishedAt"].replace("Z", "+00:00")).timestamp()
          )
          + 30,
        ),
      },
    )
    metric_rows.extend(result.get("data", {}).get("result", []))
  observed = {
    (
      x["metric"].get("service_name"),
      x["metric"].get("operation", x["metric"].get("inkcre_operation")),
    )
    for x in metric_rows
    if float(x["value"][1]) >= 1
  }
  report["signals"]["metrics"] = {
    "verified": {("inkcre.client-web", "job.submit"), ("core-py", "job.execute")}.issubset(
      observed
    ),
    "observed": sorted(observed),
    "series_count": len(metric_rows),
  }
report["verified"] = all(x["verified"] for x in report["signals"].values())
(HERE / "evidence/preview-query.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
assert report["verified"], "Preview Cloud readback is incomplete"
