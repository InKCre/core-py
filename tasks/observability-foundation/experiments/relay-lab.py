"""Hold the actual core relay and a synthetic OTLP receiver for browser acceptance."""

import importlib.util
import json
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("db_lab", HERE / "implementation-db.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)
records = []


class Receiver(BaseHTTPRequestHandler):
  def do_POST(self):
    records.append(
      {
        "path": self.path,
        "body_hex": self.rfile.read(int(self.headers["Content-Length"])).hex(),
        "server_auth_ok": self.headers.get("Authorization")
        == "Bearer synthetic-relay-ingest",
      }
    )
    self.send_response(200)
    self.send_header("Content-Type", "application/x-protobuf")
    self.send_header("Content-Length", "0")
    self.end_headers()

  def log_message(self, *args):
    pass


server = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
worker = threading.Thread(target=server.serve_forever, daemon=True)
worker.start()
env = {
  **lab.environment(),
  "SKIP_EXTENSION_START": "1",
  "OBSRV__TELEMETRY_ENABLED": "true",
  "OTEL_EXPORTER_OTLP_HEADERS": "Authorization=Bearer%20synthetic-relay-ingest",
  "PEER_ID": "00000000-0000-4000-8000-000000000002",
}
for signal_name in ("TRACES", "LOGS", "METRICS"):
  env[f"OTEL_EXPORTER_OTLP_{signal_name}_ENDPOINT"] = (
    f"http://127.0.0.1:{server.server_port}/v1/{signal_name.lower()}"
  )
  env[f"OTEL_EXPORTER_OTLP_{signal_name}_HEADERS"] = ""
with (HERE / "runtime/relay-app.log").open("w") as log:
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
    for _ in range(300):
      if process.poll() is not None:
        raise RuntimeError("Core failed; inspect local runtime log")
      try:
        if httpx.get("http://127.0.0.1:35501/readyz").status_code == 200:
          break
      except httpx.HTTPError:
        pass
      time.sleep(0.1)
    else:
      raise RuntimeError("Core readiness deadline exceeded")
    print(
      "READY: real core relay http://127.0.0.1:35501/telemetry; synthetic upstream only",
      flush=True,
    )
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    pass
  finally:
    process.send_signal(signal.SIGINT)
    process.wait(timeout=40)
    server.shutdown()
    server.server_close()
    worker.join(timeout=2)
    (HERE / "runtime/browser-real-relay.json").write_text(
      json.dumps(records, indent=2) + "\n"
    )
    print(f"Stopped; captured {len(records)} upstream batches without credential storage")
