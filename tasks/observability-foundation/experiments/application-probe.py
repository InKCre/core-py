"""Actual app lifespan and authenticated OTLP relay against the isolated task database."""

import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import psycopg
from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
  ExportTraceServiceRequest,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("db_lab", HERE / "implementation-db.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)
os.environ.update(lab.environment())
from app.middleware import create_peer_jwt

records = []
upstream_status = 200
PRIVATE = "synthetic-relay-private-ingest"


class Receiver(BaseHTTPRequestHandler):
  def do_POST(self):
    data = self.rfile.read(int(self.headers.get("Content-Length", "0")))
    records.append((self.path, data, self.headers.get("Authorization")))
    self.send_response(upstream_status)
    self.send_header("Content-Type", "application/x-protobuf")
    self.send_header("Content-Length", "0")
    self.end_headers()

  def log_message(self, *args):
    pass


server = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = "http://127.0.0.1:35501"
env = {
  **lab.environment(),
  "SKIP_EXTENSION_START": "1",
  "OTEL_EXPORTER_OTLP_TIMEOUT": "1",
  "PEER_ID": "00000000-0000-4000-8000-000000000002",
  "OTEL_EXPORTER_OTLP_HEADERS": f"Authorization=Bearer%20{PRIVATE}",
}
for name in ("TRACES", "LOGS", "METRICS"):
  env[f"OTEL_EXPORTER_OTLP_{name}_ENDPOINT"] = (
    f"http://127.0.0.1:{server.server_port}/v1/{name.lower()}"
  )
auth = {
  "Authorization": "Bearer " + create_peer_jwt(lab.CREDENTIALS["jwt"]),
  "Content-Type": "application/x-protobuf",
}
with psycopg.connect(lab.ADMIN) as connection:
  deployment_id = connection.execute(
    "SELECT value->>'deployment_id' FROM inkcre.configs WHERE key='inkcre.observability'"
  ).fetchone()[0]
report = {}
try:
  for enabled in (False, True):
    before = len(records)
    env["OBSRV__TELEMETRY_ENABLED"] = str(enabled).lower()
    with (HERE / f"runtime/application-{enabled}.log").open("w") as log:
      process = subprocess.Popen(
        [
          sys.executable,
          "-m",
          "uvicorn",
          "run:api_app",
          "--host",
          "127.0.0.1",
          "--port",
          "35501",
        ],
        cwd=ROOT,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
      )
      try:
        with httpx.Client(base_url=base, timeout=4) as client:
          deadline = time.monotonic() + 90
          while time.monotonic() < deadline:
            if process.poll() is not None:
              raise AssertionError("Application exited; inspect ignored runtime log")
            try:
              response = client.get("/readyz")
              if response.status_code == 200:
                break
            except httpx.HTTPError:
              pass
            time.sleep(0.15)
          else:
            raise AssertionError("Application did not reach ready")
          assert client.post("/telemetry/v1/traces", json={}).status_code == 401
          response = client.post("/telemetry/v1/traces", headers=auth, content=b"")
          if not enabled:
            assert response.status_code == 503
          else:
            assert response.status_code == 200 and response.content == b""
            assert (
              client.post(
                "/telemetry/v1/traces",
                headers={**auth, "Content-Type": "application/json"},
                json={},
              ).status_code
              == 415
            )
            assert (
              client.post(
                "/telemetry/v1/traces",
                headers=auth,
                content=b"\xff",
              ).status_code
              == 400
            )
            assert (
              client.post(
                "/telemetry/v1/traces",
                headers=auth,
                content=b"x" * (256 * 1024 + 1),
              ).status_code
              == 413
            )
            assert (
              client.post("/telemetry/v1/logs", headers=auth, content=b"").status_code
              == 200
            )
            assert (
              client.post(
                "/telemetry/v1/metrics",
                headers={**auth, "Content-Type": "application/x-protobuf"},
                content=b"",
              ).status_code
              == 200
            )
            upstream_status = 204
            assert (
              client.post("/telemetry/v1/logs", headers=auth, content=b"").status_code
              == 200
            )
            upstream_status = 503
            response = client.post("/telemetry/v1/traces", headers=auth, content=b"")
            assert response.status_code == 502 and PRIVATE not in response.text
            upstream_status = 200
            assert client.get("/readyz").status_code == 200
          report[str(enabled)] = {
            "ready": True,
            "unauthenticated_rejected": True,
            "relay_status": 200 if enabled else 503,
          }
      finally:
        started = time.monotonic()
        process.send_signal(signal.SIGINT)
        process.wait(timeout=40)
        report[str(enabled)]["shutdown_seconds"] = round(time.monotonic() - started, 3)
        assert process.returncode == 0
    if not enabled:
      assert len(records) == before
  assert records and all(header == f"Bearer {PRIVATE}" for _, _, header in records)
  traces = [
    MessageToDict(ExportTraceServiceRequest.FromString(body))
    for path, body, _ in records
    if path.endswith("/traces")
  ]
  rendered = json.dumps(traces)
  assert PRIVATE not in rendered and lab.CREDENTIALS["jwt"] not in rendered
  assert deployment_id in rendered
  report["checks"] = [
    "default-off makes zero OTLP requests",
    "real run.py readyz/lifespan both modes",
    "existing Peer JWT required",
    "protobuf preserved; authenticated JSON rejected with 415",
    "private server authorization only upstream",
    "400 malformed / 413 capacity / 502 upstream rejection",
    "shared deployment identity present",
    "no credentials in trace payload",
  ]
  (HERE / "evidence/application-probe.json").write_text(json.dumps(report, indent=2) + "\n")
  print(json.dumps(report, indent=2))
finally:
  server.shutdown()
  server.server_close()
  thread.join(timeout=2)
