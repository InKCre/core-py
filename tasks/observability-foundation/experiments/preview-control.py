"""Bounded PR-124 acceptance; private values stay in memory or ignored restore file."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from dotenv import dotenv_values
import httpx
import jwt

HERE = Path(__file__).resolve().parent
APP = "inkcre-core-py-pr-124"
CORE = "https://inkcre-core-py-pr-124-17b00650cc5c.herokuapp.com"
PG = "https://inkcre-postgrest-pr-124-c8a3abf570a2.herokuapp.com"
PRIVATE = HERE / "runtime/preview-restore.json"
secret = subprocess.check_output(
  ["security", "find-generic-password", "-s", "inkcre/core-py/JWT_SECRET", "-w"], text=True
).strip()
token = jwt.encode(
  {
    "role": "authenticated",
    "iss": "inkcre-peer",
    "aud": "inkcre-api",
    "iat": int(time.time()),
    "exp": int(time.time()) + 3600,
  },
  secret,
  algorithm="HS256",
)
headers = {
  "Authorization": "Bearer " + token,
  "Accept-Profile": "inkcre",
  "Content-Profile": "inkcre",
}
local = dotenv_values(HERE.parents[2] / ".env")


def request(method, url, **kwargs):
  response = httpx.request(method, url, timeout=60, **kwargs)
  if response.status_code >= 400:
    raise RuntimeError(f"HTTP {response.status_code} from {url.split('?')[0]}")
  return response


def heroku(method, path, **kwargs):
  credential = subprocess.check_output(
    ["heroku", "auth:token"], text=True, stderr=subprocess.DEVNULL
  ).strip()
  return request(
    method,
    "https://api.heroku.com/apps/" + APP + path,
    headers={
      "Authorization": "Bearer " + credential,
      "Accept": "application/vnd.heroku+json; version=3",
    },
    **kwargs,
  )


mode = sys.argv[1]
if mode == "inspect":
  config = heroku("GET", "/config-vars").json()
  shared = request(
    "GET",
    PG + "/configs?key=eq.inkcre.observability&select=key,schema,value",
    headers=headers,
  ).json()
  types = request("GET", CORE + "/job-types", headers=headers).json()
  print(
    json.dumps(
      {
        "telemetry_enabled": config.get("OBSRV__TELEMETRY_ENABLED", "false"),
        "logging_backend": config.get("OBSRV__LOGGING_BACKEND"),
        "shared_identity_present": bool(shared),
        "job_types": [x["id"] for x in types["job_types"]],
        "otlp_keys_present": sorted(k for k in config if k.startswith("OTEL_")),
      }
    )
  )
elif mode == "on":
  assert not PRIVATE.exists(), "Restore snapshot already exists"
  config = heroku("GET", "/config-vars").json()
  update = {k: v for k, v in local.items() if k.startswith("OTEL_EXPORTER_OTLP") and v}
  assert any(k.endswith("_ENDPOINT") for k in update)
  update.update(
    {
      "OBSRV__TELEMETRY_ENABLED": "true",
      "OBSRV__LOGGING_BACKEND": "postgresql",
      "OTEL_PYTHON_SDK_INTERNAL_METRICS_ENABLED": "true",
    }
  )
  shared = request(
    "GET",
    PG + "/configs?key=eq.inkcre.observability&select=key,schema,value",
    headers=headers,
  ).json()
  run_id = str(uuid.uuid4())
  PRIVATE.parent.mkdir(exist_ok=True)
  fd = os.open(PRIVATE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
  with os.fdopen(fd, "w") as stream:
    json.dump(
      {"config": {k: config.get(k) for k in update}, "shared": shared, "run_id": run_id},
      stream,
    )
  request(
    "POST",
    PG + "/configs?on_conflict=key",
    headers={**headers, "Prefer": "resolution=merge-duplicates"},
    json={
      "key": "inkcre.observability",
      "schema": "inkcre.observability.v1",
      "value": {
        "deployment_id": run_id,
        "otlp_http_endpoints": None,
        "diagnostics_url": None,
      },
    },
  )
  heroku("PATCH", "/config-vars", json=update)
  print(
    json.dumps(
      {"preview_enabled": True, "deployment_id": run_id, "app": APP, "restore_saved": True}
    )
  )
elif mode == "healthy":
  assert PRIVATE.exists()
  heroku(
    "PATCH",
    "/config-vars",
    json={k: v for k, v in local.items() if k.startswith("OTEL_EXPORTER_OTLP") and v},
  )
  print(json.dumps({"preview_upstream_restored": True}))
elif mode == "disable":
  heroku("PATCH", "/config-vars", json={"OBSRV__TELEMETRY_ENABLED": "false"})
  print(json.dumps({"preview_telemetry_enabled": False, "logging_backend": "postgresql"}))
elif mode == "fault":
  assert PRIVATE.exists()
  heroku(
    "PATCH",
    "/config-vars",
    json={
      f"OTEL_EXPORTER_OTLP_{signal}_ENDPOINT": f"http://127.0.0.1:9/v1/{signal.lower()}"
      for signal in ("TRACES", "LOGS", "METRICS")
    },
  )
  print(json.dumps({"preview_upstream_fault": "loopback_refused"}))
elif mode == "off":
  saved = json.loads(PRIVATE.read_text())
  heroku("PATCH", "/config-vars", json=saved["config"])
  if saved["shared"]:
    request(
      "POST",
      PG + "/configs?on_conflict=key",
      headers={**headers, "Prefer": "resolution=merge-duplicates"},
      json=saved["shared"][0],
    )
  else:
    request("DELETE", PG + "/configs?key=eq.inkcre.observability", headers=headers)
  for attempt in range(6):
    config = heroku("GET", "/config-vars").json()
    if all(config.get(k) == v for k, v in saved["config"].items()):
      break
    time.sleep(2)
  else:
    raise RuntimeError("Preview configuration restore did not converge")
  print(
    json.dumps(
      {
        "restored": True,
        "telemetry_enabled": config.get("OBSRV__TELEMETRY_ENABLED", "false"),
        "private_export_keys_removed": all(
          not config.get(k)
          for k, v in saved["config"].items()
          if k.startswith("OTEL_EXPORTER_OTLP") and v is None
        ),
      }
    )
  )
elif mode == "ready":
  r = httpx.get(CORE + "/readyz", timeout=60)
  print(json.dumps({"ready_status": r.status_code}))
