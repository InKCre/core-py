"""Disposable PostgreSQL and real HTTP verification of production runtime boundaries."""

import asyncio
from contextlib import redirect_stderr
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import runpy
import socket
import sys
import threading
import time
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
LAB = runpy.run_path(str(HERE / "implementation-db.py"))
os.environ.update(LAB["environment"]())
assert "@127.0.0.1:35432/o11y_impl" in os.environ["DATABASE_URL"]
os.environ["OBSRV__LOGGING_BACKEND"] = "postgresql"
os.environ["OBSRV__TELEMETRY_ENABLED"] = "false"

import fastapi
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import (
  ExportMetricsServiceRequest,
)
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
  ExportTraceServiceRequest,
)
import psycopg
import pydantic
import uvicorn

from libs.obsrv.main import setup_obsrv, start_obsrv, close_obsrv
from libs.obsrv.log_record import TRACE_ID
from libs.obsrv.telemetry import close_telemetry, is_enabled, start_telemetry

LOGGER = setup_obsrv()
from app.business.job import JobHandler, JobManager
from app.business.agent import (
  BoundAgentTool,
  InMemoryThreadPersistenceBackend,
  Thread,
  ThreadState,
)
from app.business.agent.contracts import ToolExecutionError
from app.schemas.ai import FunctionTool, ToolCall
from app.business.peer.http import PeerHTTPOutbound
from app.business.peer.contracts import PeerRequestNotExecuted
from app.engine import ASYNC_DB_ENGINE
from app.middleware import require_peer_jwt
from app.observability import TelemetryMiddleware
from app.scheduler import start_scheduler, drain_scheduler, scheduler, with_trace_id
from app.schemas.job import JobStatus
from app.schemas.peer import PeerModel, PEER_EXECUTION_HEADER

METRICS_ONLY = "--metrics-only" in sys.argv
RUN = uuid.uuid4().hex
CANARY = "runtime-private-content-" + RUN
JOB_TYPE = "lab.observability.runtime." + RUN
records = []
seen_legacy_ids = []
handler_started = asyncio.Event()


class Receiver(BaseHTTPRequestHandler):
  def do_POST(self):
    records.append((self.path, self.rfile.read(int(self.headers["Content-Length"]))))
    self.send_response(200)
    self.send_header("Content-Length", "0")
    self.end_headers()

  def log_message(self, *args):
    pass


class Parameters(pydantic.BaseModel):
  mode: str = "success"


class Handler(
  JobHandler[Parameters],
  job_type=JOB_TYPE,
  description="Disposable telemetry boundary probe",
  parameters_model=Parameters,
  default_timeout_seconds=10,
):
  @classmethod
  async def can_handle(cls, parameters):
    return True

  @classmethod
  async def handle(cls, job, parameters):
    seen_legacy_ids.append(TRACE_ID.get())
    LOGGER.info(CANARY)
    if parameters.mode == "failure":
      raise RuntimeError(CANARY)
    if parameters.mode == "wait":
      handler_started.set()
      await asyncio.Event().wait()
    job.state = {"finished": True}


def spans():
  return [
    span
    for path, body in records
    if path.endswith("traces")
    for resource in ExportTraceServiceRequest.FromString(body).resource_spans
    for scope in resource.scope_spans
    for span in scope.spans
  ]


def attributes(span):
  return {
    attr.key: getattr(attr.value, attr.value.WhichOneof("value"))
    for attr in span.attributes
  }


async def execute(job):
  assert job.id is not None
  assert await with_trace_id(f"job.{job.id}", JobManager.run)(job.id)
  saved = await JobManager.get(job.id)
  assert saved is not None
  return saved


async def main():
  receiver = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
  threading.Thread(target=receiver.serve_forever, daemon=True).start()
  endpoint = f"http://127.0.0.1:{receiver.server_port}/v1/"
  for signal in ("TRACES", "LOGS", "METRICS"):
    os.environ[f"OTEL_EXPORTER_OTLP_{signal}_ENDPOINT"] = (
      "" if METRICS_ONLY and signal != "METRICS" else endpoint + signal.lower()
    )
  diagnostics = io.StringIO()
  start_obsrv()
  start_scheduler()
  await JobManager.sync_job_types()

  # Endpoints alone do not enable telemetry; the existing PG writer is still active.
  start_telemetry(enabled=False, service_version="runtime-probe")
  off_job = await JobManager.create(JOB_TYPE, {"mode": "success"})
  off_job = await execute(off_job)
  assert off_job.status == JobStatus.FINISHED and off_job.submission_traceparent is None
  assert not records and not is_enabled()
  off_submit_on_execute = await JobManager.create(JOB_TYPE, {"mode": "success"})

  start_telemetry(enabled=True, service_version="runtime-probe")
  linked = await JobManager.create(JOB_TYPE, {"mode": "success"})
  linked = await execute(linked)
  assert linked.status == JobStatus.FINISHED
  assert bool(linked.submission_traceparent) is not METRICS_ONLY
  no_link = await execute(off_submit_on_execute)
  assert no_link.submission_traceparent is None
  failed = await JobManager.create(JOB_TYPE, {"mode": "failure"})
  failed = await execute(failed)
  assert failed.status == JobStatus.FAILED and failed.state["error"] == CANARY
  cancelled = await JobManager.create(JOB_TYPE, {"mode": "wait"})
  task = asyncio.create_task(
    with_trace_id(f"job.{cancelled.id}", JobManager.run)(cancelled.id)
  )
  await asyncio.wait_for(handler_started.wait(), timeout=5)
  await JobManager.abort(cancelled.id)
  await JobManager.check_abort_requests()
  assert await task
  cancelled = await JobManager.get(cancelled.id)
  assert cancelled.status == JobStatus.ABORTED
  on_submit_off_execute = await JobManager.create(JOB_TYPE, {"mode": "success"})
  persisted_parent = on_submit_off_execute.submission_traceparent
  assert bool(persisted_parent) is not METRICS_ONLY

  # Concurrent production Tool scopes retain independent success/error outcomes.
  entered = 0
  overlapped = asyncio.Event()

  async def tool_handler(parameters):
    nonlocal entered
    entered += 1
    if entered == 2:
      overlapped.set()
    await asyncio.wait_for(overlapped.wait(), 2)
    if parameters.mode == "failure":
      raise ToolExecutionError({"detail": CANARY})
    return {"finished": True}

  backend = InMemoryThreadPersistenceBackend()
  tool = BoundAgentTool(
    FunctionTool(
      id="lab.boundary",
      description="Synthetic outcome probe",
      input_schema=Parameters.model_json_schema(),
    ),
    Parameters,
    tool_handler,
  )
  identifier, state = await backend.create(
    ThreadState(
      model=1,
      tools=(tool.definition,),
      tool_choice="auto",
      max_model_calls_per_turn=1,
      messages=(),
    )
  )
  thread = Thread(identifier, state, backend, (tool,))
  tool_results = await asyncio.gather(
    *(
      thread._execute_tool_call(
        ToolCall(id=mode, tool=tool.definition.id, arguments={"mode": mode})
      )
      for mode in ("success", "failure")
    )
  )
  assert overlapped.is_set() and [result.is_error for result in tool_results] == [
    False,
    True,
  ]

  # Production Peer outbound and ASGI telemetry middleware over actual loopback TCP.
  app = fastapi.FastAPI()
  app.add_middleware(TelemetryMiddleware)
  requests = []

  @app.post("/peer/{item}", dependencies=[fastapi.Depends(require_peer_jwt)])
  async def peer_route(item: str, request: fastapi.Request):
    requests.append({"item": item, "traceparent": request.headers.get("traceparent")})
    await request.json()
    if item == "not-executed":
      return fastapi.responses.JSONResponse(
        {"detail": CANARY},
        status_code=503,
        headers={PEER_EXECUTION_HEADER: "not-executed"},
      )
    return fastapi.responses.JSONResponse(
      {"result": CANARY}, status_code=500 if item == "failed" else 200
    )

  sock = socket.socket()
  sock.bind(("127.0.0.1", 0))
  port = sock.getsockname()[1]
  config = uvicorn.Config(app, log_level="critical", access_log=False, lifespan="off")
  server = uvicorn.Server(config)
  serving = asyncio.create_task(server.serve(sockets=[sock]))
  async with asyncio.timeout(5):
    while not server.started:
      await asyncio.sleep(0.01)
  peer = PeerModel(id=uuid.uuid4(), name="runtime-probe")

  async def call_peer(item):
    outbound = PeerHTTPOutbound(
      peer, {"method": "POST", "url": f"http://127.0.0.1:{port}/peer/{item}"}
    )
    payload = {
      "body": {"private": CANARY},
      "query": {"private": [CANARY]},
      "headers": {"x-private": [CANARY], "traceparent": [CANARY], "tracestate": [CANARY]},
    }
    if item == "not-executed":
      try:
        await outbound.execute(payload)
        raise AssertionError("not-executed must retain its production error")
      except PeerRequestNotExecuted:
        pass
    else:
      result = await outbound.execute(payload)
      assert result["status"] == (500 if item == "failed" else 200)

  await asyncio.gather(*(call_peer(item) for item in (CANARY, "failed", "not-executed")))
  assert len(requests) == 3
  assert all(
    r["traceparent"] == CANARY if METRICS_ONLY else r["traceparent"].startswith("00-")
    for r in requests
  )
  server.should_exit = True
  await serving
  sock.close()
  await close_telemetry()

  # A new off execution retains the previously captured carrier, including at close.
  before = len(records)
  preserved = await execute(on_submit_off_execute)
  assert preserved.status == JobStatus.FINISHED
  assert preserved.submission_traceparent == persisted_parent and len(records) == before

  # Receiver failure cannot alter the durable Job result or PostgreSQL logging.
  unused = socket.socket()
  unused.bind(("127.0.0.1", 0))
  refused_port = unused.getsockname()[1]
  unused.close()
  for signal in ("TRACES", "LOGS", "METRICS"):
    os.environ[f"OTEL_EXPORTER_OTLP_{signal}_ENDPOINT"] = (
      ""
      if METRICS_ONLY and signal != "METRICS"
      else f"http://127.0.0.1:{refused_port}/v1/{signal.lower()}"
    )
  with redirect_stderr(diagnostics):
    start_telemetry(enabled=True, service_version="runtime-probe")
    outage = await JobManager.create(JOB_TYPE, {"mode": "success"})
    outage = await execute(outage)
    start = time.monotonic()
    await close_telemetry()
    outage_close = time.monotonic() - start
  assert outage.status == JobStatus.FINISHED and outage_close < 5
  assert CANARY not in diagnostics.getvalue()
  await close_obsrv()
  await drain_scheduler()
  scheduler.shutdown(wait=False)
  await ASYNC_DB_ENGINE.dispose()
  receiver.shutdown()
  receiver.server_close()

  exported = spans()
  assert all(CANARY.encode() not in body for _, body in records)
  server_spans = []
  client_spans = []
  if METRICS_ONLY:
    assert not exported
  else:
    by_job = {}
    for span in exported:
      if span.name in ("job.submit", "job.execute"):
        by_job.setdefault(attributes(span)["inkcre.job.id"], {})[span.name] = span
    submitted = by_job[linked.id]["job.submit"]
    executed = by_job[linked.id]["job.execute"]
    assert executed.trace_id != submitted.trace_id and not executed.parent_span_id
    assert len(executed.links) == 1
    assert executed.links[0].trace_id == submitted.trace_id
    assert executed.links[0].span_id == submitted.span_id
    assert not by_job[no_link.id]["job.execute"].links
    assert "job.execute" not in by_job[preserved.id]
    for span in exported:
      assert not span.events and not span.status.message
    assert all(CANARY.encode() not in body for _, body in records)
    server_spans = [span for span in exported if span.name == "http.server"]
    client_spans = [span for span in exported if span.name == "peer.http"]
    assert len(server_spans) == len(client_spans) == 3
    assert all(attributes(span)["http.route"] == "/peer/{item}" for span in server_spans)
    assert all(
      any(
        server_span.parent_span_id == client.span_id
        and server_span.trace_id == client.trace_id
        for client in client_spans
      )
      for server_span in server_spans
    )
  job_ids = [
    off_job.id,
    linked.id,
    no_link.id,
    failed.id,
    cancelled.id,
    preserved.id,
    outage.id,
  ]
  assert seen_legacy_ids == [f"job.{job_id}" for job_id in job_ids]
  with psycopg.connect(LAB["ADMIN"]) as conn:
    pg_logs = conn.execute(
      "SELECT trace_id, body FROM inkcre.logs WHERE body=%s", (CANARY,)
    ).fetchall()
    assert {row[0] for row in pg_logs} == {f"job.{job_id}" for job_id in job_ids}
  capacity_rejected = []
  for column in ("submission_traceparent", "submission_tracestate"):
    try:
      with psycopg.connect(LAB["ADMIN"]) as conn:
        conn.execute(
          psycopg.sql.SQL("UPDATE inkcre.jobs SET {}=%s WHERE id=%s").format(
            psycopg.sql.Identifier(column)
          ),
          ("x" * 513, off_job.id),
        )
      raise AssertionError("database accepted over-capacity carrier")
    except psycopg.errors.CheckViolation:
      capacity_rejected.append(column)
  counts = {}
  duration_counts = {}
  for path, body in records:
    if not path.endswith("metrics"):
      continue
    batch = ExportMetricsServiceRequest.FromString(body)
    for resource in batch.resource_metrics:
      for scope in resource.scope_metrics:
        for metric in scope.metrics:
          if metric.name not in ("inkcre.operation.count", "inkcre.operation.duration"):
            continue
          points = (
            metric.sum.data_points
            if metric.HasField("sum")
            else metric.histogram.data_points
          )
          for point in points:
            labels = {attr.key: attr.value.string_value for attr in point.attributes}
            assert set(labels) == {"operation", "outcome"}
            key = labels["operation"] + ":" + labels["outcome"]
            target = counts if metric.HasField("sum") else duration_counts
            value = point.as_int if metric.HasField("sum") else point.count
            target[key] = max(value, target.get(key, 0))
  expected = {
    "job.submit:success": 4,
    "job.execute:success": 2,
    "job.execute:error": 1,
    "job.execute:cancelled": 1,
    "http.server:success": 1,
    "http.server:error": 2,
    "peer.http:success": 1,
    "peer.http:error": 2,
    "agent.tool:success": 1,
    "agent.tool:error": 1,
  }
  assert counts == expected, counts
  assert duration_counts == expected, duration_counts
  evidence = {
    "run_id": RUN,
    "signal_mode": "metrics-only" if METRICS_ONLY else "traces-logs-metrics",
    "operation_counts": counts,
    "duration_sample_counts": duration_counts,
    "concurrent_tool_outcomes_isolated": True,
    "scope": (
      "disposable PostgreSQL + production Job/PG log/Peer HTTP/ASGI mechanisms; "
      "not full runtime or SaaS"
    ),
    "job_ids": job_ids,
    "job_statuses": [
      str(job.status)
      for job in (off_job, linked, no_link, failed, cancelled, preserved, outage)
    ],
    "off_with_endpoints_no_export": True,
    "independent_execution_trace_with_submission_link": not METRICS_ONLY,
    "off_submit_on_execute_no_link": True,
    "on_submit_off_execute_carrier_preserved": True,
    "postgresql_log_rows": len(pg_logs),
    "legacy_job_trace_ids_preserved": True,
    "carrier_capacity_rejected": capacity_rejected,
    "http_requests": len(requests),
    "http_client_spans": len(client_spans),
    "http_server_spans": len(server_spans),
    "http_parent_child_propagation": not METRICS_ONLY,
    "http_errors_not_retried": True,
    "canary_absent_at_first_otlp_export": True,
    "outage_job_finished": True,
    "outage_shutdown_seconds": outage_close,
    "trace_spans": len(exported),
    "otlp_requests": len(records),
  }
  destination = (
    HERE
    / "evidence"
    / ("runtime-probe-metrics-only.json" if METRICS_ONLY else "runtime-probe.json")
  )
  destination.write_text(json.dumps(evidence, indent=2) + "\n")
  print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
  asyncio.run(main())
