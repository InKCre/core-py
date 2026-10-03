"""Assert Cloud-stored browser histogram interoperates with Core's published stream."""

from datetime import datetime
import json
from pathlib import Path

from dotenv import dotenv_values
import httpx

HERE = Path(__file__).resolve().parent
config = dotenv_values(HERE.parents[2] / ".env")
probe = json.loads((HERE / "evidence/preview-metric-parity.json").read_text())
with httpx.Client(
  base_url=config["GRAFANA_URL"],
  headers={"Authorization": "Bearer " + config["GRAFANA_SERVICE_ACCOUNT_TOKEN"]},
  timeout=30,
) as client:
  catalog = client.get("/api/datasources")
  assert catalog.status_code == 200
  uid = next(
    x["uid"]
    for x in catalog.json()
    if x["type"] == "prometheus" and x["name"].endswith("-prom")
  )
  response = client.get(
    "/api/datasources/proxy/uid/" + uid + "/api/v1/query",
    params={
      "query": (
        '{__name__=~"inkcre_operation_duration_seconds_(bucket|count|sum)",'
        'service_version="'
      )
      + probe["version"]
      + '"}',
      "time": int(
        datetime.fromisoformat(probe["finishedAt"].replace("Z", "+00:00")).timestamp()
      )
      + 10,
    },
  )
  assert response.status_code == 200
  series = response.json().get("data", {}).get("result", [])
  assert series, "Browser histogram absent"
  assert len({x["metric"]["service_instance_id"] for x in series}) == 1
  assert all(
    x["metric"].get("operation") == "job.submit"
    and x["metric"].get("outcome") == "success"
    and "inkcre_operation" not in x["metric"]
    for x in series
  ), "Cross-Peer metric labels differ"
  buckets = sorted(
    (float(x["metric"]["le"]), float(x["value"][1]))
    for x in series
    if x["metric"]["__name__"].endswith("_bucket")
  )
  expected = [
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1,
    2.5,
    5,
    10,
    30,
    60,
    300,
    float("inf"),
  ]
  assert [b for b, _ in buckets] == expected, "Cross-Peer histogram boundaries differ"
  assert all(a[1] <= b[1] for a, b in zip(buckets, buckets[1:])) and buckets[-1][1] == 1
  count = next(
    float(x["value"][1]) for x in series if x["metric"]["__name__"].endswith("_count")
  )
  total = next(
    float(x["value"][1]) for x in series if x["metric"]["__name__"].endswith("_sum")
  )
  assert count == 1 and total > 0
report = {
  "verified": True,
  "source": probe["source"],
  "labels": {"operation": "job.submit", "outcome": "success"},
  "count": count,
  "sum_seconds": total,
  "buckets": [{"le": str(b), "count": c} for b, c in buckets],
}
(HERE / "evidence/preview-metric-query.json").write_text(
  json.dumps(report, indent=2) + "\n"
)
print(json.dumps(report))
