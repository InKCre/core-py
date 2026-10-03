"""Real OTLP boundary probe plus temporary SDK fault injection; no external credentials."""

import asyncio
from contextlib import ExitStack, redirect_stderr
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import logging
import os
from pathlib import Path
import sys
import threading
from tempfile import TemporaryDirectory
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
os.environ["INKCRE_ENV_FILE"] = ""
os.environ["OTEL_EXPORTER_OTLP_TIMEOUT"] = "1"
for _signal in ("TRACES", "LOGS", "METRICS"):
  os.environ[f"OTEL_EXPORTER_OTLP_{_signal}_TIMEOUT"] = "1"
os.environ["OTEL_PYTHON_SDK_INTERNAL_METRICS_ENABLED"] = "true"

from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import (
  ExportMetricsServiceRequest,
)
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
  ExportTraceServiceRequest,
)
from opentelemetry.trace import (
  NonRecordingSpan,
  SpanContext,
  TraceState,
  get_current_span,
  use_span,
)
from libs.obsrv import telemetry

CANARY = "foundation-private-content-should-not-export"
records = []
delay = 0.0


class Receiver(BaseHTTPRequestHandler):
  def do_POST(self):
    body = self.rfile.read(int(self.headers["Content-Length"]))
    records.append((self.path, body, self.headers.get("Authorization")))
    if self.path == "/default-timeout/traces":
      time.sleep(1.2)
    elif delay and not self.path.endswith("metrics"):
      time.sleep(delay)
    self.send_response(200)
    self.send_header("Content-Length", "0")
    self.end_headers()

  def log_message(self, *args):
    pass


def points(metrics, name):
  for item in metrics:
    for resource in item.get("resourceMetrics", []):
      for scope in resource["scopeMetrics"]:
        for metric in scope["metrics"]:
          if metric["name"] == name:
            yield from metric.get("sum", metric.get("histogram"))["dataPoints"]


def labels(point):
  return {a["key"]: next(iter(a["value"].values())) for a in point["attributes"]}


async def injected_faults(endpoint, diagnostic):
  from opentelemetry.sdk.trace import TracerProvider, Span as SDKSpan
  from opentelemetry.sdk._logs import LoggerProvider
  from opentelemetry.sdk.metrics import MeterProvider
  from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
  from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
  from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

  failure = RuntimeError(CANARY)
  closed = []
  checks = []
  for signal, provider, method, exporter in (
    ("traces", TracerProvider, "get_tracer", OTLPSpanExporter),
    ("logs", LoggerProvider, "get_logger", OTLPLogExporter),
    ("metrics", MeterProvider, "get_meter", OTLPMetricExporter),
  ):
    for item in ("traces", "logs", "metrics"):
      os.environ[f"OTEL_EXPORTER_OTLP_{item.upper()}_ENDPOINT"] = (
        endpoint + "/fault/" + item if item == signal else ""
      )
    before = {
      thread.ident for thread in threading.enumerate() if thread.name.startswith("Otel")
    }
    original_shutdown = exporter.shutdown

    def observed_shutdown(self, *args, **kwargs):
      closed.append(signal)
      return original_shutdown(self, *args, **kwargs)

    with redirect_stderr(diagnostic), patch.object(provider, method, side_effect=failure):
      with patch.object(exporter, "shutdown", new=observed_shutdown):
        telemetry.start_telemetry(enabled=True, service_version="fault-probe")
      assert not telemetry.is_enabled()
      assert telemetry.get_export_connection(signal) is None
    assert closed[-1] == signal
    assert {
      thread.ident for thread in threading.enumerate() if thread.name.startswith("Otel")
    } == before
    checks.append(signal + "_initialization_rollback")

  for signal in ("TRACES", "LOGS", "METRICS"):
    os.environ[f"OTEL_EXPORTER_OTLP_{signal}_ENDPOINT"] = (
      endpoint + "/fault/" + signal.lower()
    )
  with (
    redirect_stderr(diagnostic),
    patch.object(TracerProvider, "get_tracer", side_effect=failure),
  ):
    telemetry.start_telemetry(enabled=True, service_version="fault-probe")
  assert telemetry.is_enabled() and telemetry.get_export_connection("traces") is None
  assert telemetry.get_export_connection("logs") and telemetry.get_export_connection(
    "metrics"
  )
  await telemetry.close_telemetry()
  checks.append("failed_signal_not_published_with_other_signals_active")

  with redirect_stderr(diagnostic):
    telemetry.start_telemetry(enabled=True, service_version="fault-probe")
    runtime = telemetry._runtime
    with patch.object(runtime.tracer, "start_span", side_effect=failure):
      with telemetry.operation("ai.chat") as observation:
        assert isinstance(observation.span, NonRecordingSpan)
        business_result = 42
    assert business_result == 42
    checks.append("start_span_failure_isolated")
    with patch.object(telemetry, "use_span", side_effect=failure):
      with telemetry.operation("ai.chat"):
        business_result = 43
    assert business_result == 43
    checks.append("context_activation_failure_isolated")
    with ExitStack() as faults:
      for target, method in (
        (runtime.logger, "emit"),
        (runtime.tokens, "add"),
        (runtime.missing_usage, "add"),
      ):
        faults.enter_context(patch.object(target, method, side_effect=failure))
      telemetry.emit_event("ai.finished", {})
      telemetry.record_ai_usage("chat", 1, None)
    checks.append("log_and_usage_failure_isolated")
    for business_error in (None, LookupError(CANARY), asyncio.CancelledError(CANARY)):
      with ExitStack() as faults:
        for target, method in (
          (SDKSpan, "set_attribute"),
          (SDKSpan, "set_status"),
          (SDKSpan, "end"),
          (runtime.operations, "add"),
          (runtime.duration, "record"),
        ):
          faults.enter_context(patch.object(target, method, side_effect=failure))
        try:
          with telemetry.operation("ai.chat") as observation:
            observation.outcome = "error"
            if business_error is not None:
              raise business_error
            business_result = 44
        except BaseException as observed:
          assert observed is business_error
        else:
          assert business_error is None and business_result == 44
      observation.span.end()
    checks.append("finalization_preserves_result_exception_and_cancellation")
    await telemetry.close_telemetry()
  assert CANARY not in diagnostic.getvalue()
  return checks


async def timeout_configuration(endpoint, diagnostic):
  timeout_keys = ["OTEL_EXPORTER_OTLP_TIMEOUT"] + [
    f"OTEL_EXPORTER_OTLP_{signal}_TIMEOUT" for signal in ("TRACES", "LOGS", "METRICS")
  ]
  snapshots = {}
  with patch.dict(os.environ), TemporaryDirectory() as temporary:
    for key in timeout_keys:
      os.environ.pop(key, None)
    for signal in ("TRACES", "LOGS", "METRICS"):
      os.environ[f"OTEL_EXPORTER_OTLP_{signal}_ENDPOINT"] = (
        endpoint + "/timeout/" + signal.lower()
      )

    async def capture(label):
      with redirect_stderr(diagnostic):
        telemetry.start_telemetry(enabled=True, service_version="timeout-probe")
        snapshots[label] = {
          signal: connection[2]
          if (connection := telemetry.get_export_connection(signal))
          else None
          for signal in ("traces", "logs", "metrics")
        }
        with telemetry.operation("ai.chat"):
          business_result = 42
        await telemetry.close_telemetry()
      assert business_result == 42

    os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = endpoint + "/default-timeout/traces"
    before = len(records)
    await capture("default")
    assert snapshots["default"] == {"traces": 10, "logs": 10, "metrics": 10}
    exported = [
      MessageToDict(ExportMetricsServiceRequest.FromString(body))
      for path, body, _ in records[before:]
      if path.endswith("metrics")
    ]
    delivered = list(points(exported, "otel.sdk.exporter.span.exported"))
    assert delivered and all("error.type" not in labels(point) for point in delivered)
    snapshots["default_slow_receiver"] = {
      "delay_seconds": 1.2,
      "successful_spans": sum(int(point["asInt"]) for point in delivered),
    }
    os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = endpoint + "/timeout/traces"
    dotenv = Path(temporary) / "probe.env"
    dotenv.write_text(
      "OTEL_EXPORTER_OTLP_TIMEOUT=2.5\nOTEL_EXPORTER_OTLP_TRACES_TIMEOUT=3.5\n"
    )
    os.environ["INKCRE_ENV_FILE"] = str(dotenv)
    os.environ["OTEL_EXPORTER_OTLP_TIMEOUT"] = "4"
    os.environ["OTEL_EXPORTER_OTLP_METRICS_TIMEOUT"] = "6"
    await capture("dotenv_signal_and_environment_common")
    assert snapshots["dotenv_signal_and_environment_common"] == {
      "traces": 3.5,
      "logs": 4,
      "metrics": 6,
    }
    os.environ["OTEL_EXPORTER_OTLP_TRACES_TIMEOUT"] = "7"
    await capture("environment_signal_over_dotenv")
    assert snapshots["environment_signal_over_dotenv"] == {
      "traces": 7,
      "logs": 4,
      "metrics": 6,
    }
    for invalid in ("0", "-1", "31", "nan", "inf", "invalid"):
      os.environ["OTEL_EXPORTER_OTLP_TRACES_TIMEOUT"] = invalid
      await capture("invalid_" + invalid)
      assert snapshots["invalid_" + invalid] == {"traces": None, "logs": 4, "metrics": 6}
    os.environ["OTEL_EXPORTER_OTLP_TIMEOUT"] = "invalid"
    os.environ["OTEL_EXPORTER_OTLP_TRACES_TIMEOUT"] = "30"
    await capture("valid_signal_over_invalid_common")
    assert snapshots["valid_signal_over_invalid_common"] == {
      "traces": 30,
      "logs": None,
      "metrics": 6,
    }
  return snapshots


async def main():
  global delay
  logging.getLogger().addHandler(logging.NullHandler())
  server = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
  worker = threading.Thread(target=server.serve_forever, daemon=True)
  worker.start()
  endpoint = f"http://127.0.0.1:{server.server_port}"
  for signal in ("TRACES", "LOGS", "METRICS"):
    os.environ[f"OTEL_EXPORTER_OTLP_{signal}_ENDPOINT"] = (
      f"{endpoint}/custom/{signal.lower()}"
    )
  os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = (
    "Authorization=Bearer%20synthetic-private-write-token"
  )
  os.environ["OTEL_RESOURCE_ATTRIBUTES"] = f"forbidden={CANARY}"
  before_threads = {t.ident for t in threading.enumerate()}
  telemetry.start_telemetry(enabled=False, service_version="probe")
  with telemetry.operation("ai.chat") as observation:
    assert isinstance(observation.span, NonRecordingSpan)
    assert get_current_span() is observation.span
    telemetry.emit_event("ai.finished", {"operation": "chat"})
    telemetry.record_ai_usage("chat", 1, 2)
  parent = NonRecordingSpan(SpanContext(trace_id=123, span_id=456, is_remote=False))
  with use_span(parent):
    with telemetry.operation("ai.chat") as observation:
      assert get_current_span() is parent and observation.span is not parent
  await telemetry.close_telemetry()
  assert not telemetry.is_enabled() and records == []
  assert telemetry.get_export_connection("traces") is None
  assert {t.ident for t in threading.enumerate()} == before_threads

  diagnostic = io.StringIO()
  with redirect_stderr(diagnostic):
    telemetry.start_telemetry(
      enabled=True,
      service_version="probe",
      resource_attributes={"inkcre.deployment.id": "synthetic-deployment"},
      endpoints={"traces": endpoint + "/wrong-default"},
    )
    assert telemetry.is_enabled()
    connection = telemetry.get_export_connection("traces")
    assert connection is not None and connection[0] == endpoint + "/custom/traces"
    connection[1]["authorization"] = "changed-copy"
    assert telemetry.get_export_connection("traces")[1]["authorization"] != "changed-copy"
    with telemetry.operation("ai.chat", attributes={"gen_ai.operation.name": "chat"}):
      telemetry.emit_event("ai.finished", {"gen_ai.usage.input_tokens": 3})
      telemetry.record_ai_usage("chat", 3, None)
      logging.getLogger("inkcre").warning(CANARY)
      logging.getLogger("opentelemetry.trace.span").warning(CANARY)
      TraceState.from_header([CANARY])
    try:
      with telemetry.operation("ai.chat") as observation:
        observation.outcome = "cancelled"
        raise RuntimeError(CANARY)
    except RuntimeError:
      pass
    try:
      with telemetry.operation("ai.chat") as observation:
        observation.outcome = "error"
        raise asyncio.CancelledError(CANARY)
    except asyncio.CancelledError:
      pass
    with telemetry.operation("agent.tool") as observation:
      observation.outcome = "error"
    telemetry.record_ai_usage("embeddings", 0, -1)
    started = time.monotonic()
    await telemetry.close_telemetry()
    healthy_close = time.monotonic() - started
  assert CANARY not in diagnostic.getvalue()
  assert healthy_close < 5, healthy_close
  assert {r[0] for r in records} == {"/custom/traces", "/custom/logs", "/custom/metrics"}
  assert all(CANARY.encode() not in r[1] for r in records)
  assert all(r[2] == "Bearer synthetic-private-write-token" for r in records)
  decoded = {"traces": [], "logs": [], "metrics": []}
  classes = {
    "traces": ExportTraceServiceRequest,
    "logs": ExportLogsServiceRequest,
    "metrics": ExportMetricsServiceRequest,
  }
  for path, data, _ in records:
    signal = path.rsplit("/", 1)[-1]
    decoded[signal].append(MessageToDict(classes[signal].FromString(data)))
  spans = [
    span
    for req in decoded["traces"]
    for rs in req["resourceSpans"]
    for scope in rs["scopeSpans"]
    for span in scope["spans"]
  ]
  assert len(spans) == 4
  assert all(
    not span.get("events") and not span.get("status", {}).get("message") for span in spans
  )
  logs = [
    log
    for req in decoded["logs"]
    for rs in req["resourceLogs"]
    for scope in rs["scopeLogs"]
    for log in scope["logRecords"]
  ]
  assert len(logs) == 1 and logs[0]["body"]["stringValue"] == "ai.finished"
  assert logs[0]["traceId"] in {span["traceId"] for span in spans}
  token_points = list(points(decoded["metrics"], "inkcre.ai.token.usage"))
  missing_points = list(points(decoded["metrics"], "inkcre.ai.usage.missing"))
  assert len(token_points) == 2 and sorted(int(p["asInt"]) for p in token_points) == [0, 3]
  assert sum(int(p["asInt"]) for p in missing_points) == 2
  duration_points = list(points(decoded["metrics"], "inkcre.operation.duration"))
  assert duration_points and all(
    point["explicitBounds"][0] <= 0.005 and point["explicitBounds"][-1] >= 300
    for point in duration_points
  ), "Duration buckets must cover millisecond HTTP calls and multi-minute Jobs"
  operation_points = list(points(decoded["metrics"], "inkcre.operation.count"))
  assert {labels(p)["outcome"] for p in operation_points} == {
    "success",
    "error",
    "cancelled",
  }
  assert sum(int(p["asInt"]) for p in operation_points) == 4
  assert all(set(labels(p)) == {"operation", "outcome"} for p in operation_points)

  for signal in ("TRACES", "LOGS", "METRICS"):
    os.environ[f"OTEL_EXPORTER_OTLP_{signal}_ENDPOINT"] = (
      f"http://user:{CANARY}@localhost/ingest"
    )
  with redirect_stderr(diagnostic):
    telemetry.start_telemetry(enabled=True, service_version="probe")
  assert not telemetry.is_enabled() and CANARY not in diagnostic.getvalue()

  for signal in ("TRACES", "LOGS", "METRICS"):
    os.environ[f"OTEL_EXPORTER_OTLP_{signal}_ENDPOINT"] = (
      f"{endpoint}/slow/{signal.lower()}"
    )
  # Invalid secret headers are rejected without printing their raw value.
  os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = CANARY
  with redirect_stderr(diagnostic):
    telemetry.start_telemetry(enabled=True, service_version="probe")
  assert not telemetry.is_enabled() and CANARY not in diagnostic.getvalue()
  os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = "Authorization=synthetic"

  # A single configured signal does not initialize the other signal workers.
  os.environ["OTEL_EXPORTER_OTLP_LOGS_ENDPOINT"] = ""
  os.environ["OTEL_EXPORTER_OTLP_METRICS_ENDPOINT"] = ""
  count = len(records)
  with redirect_stderr(diagnostic):
    telemetry.start_telemetry(enabled=True, service_version="probe")
    with telemetry.operation("ai.chat"):
      telemetry.emit_event("ai.finished", {})
      telemetry.record_ai_usage("chat", 1, 1)
    await telemetry.close_telemetry()
  assert len(records) == count + 1 and records[-1][0].endswith("traces")

  # A real refused connection must not change the operation result.
  unused = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
  refused = f"http://127.0.0.1:{unused.server_port}/ingest"
  unused.server_close()
  for signal in ("TRACES", "LOGS", "METRICS"):
    os.environ[f"OTEL_EXPORTER_OTLP_{signal}_ENDPOINT"] = refused
  with redirect_stderr(diagnostic):
    telemetry.start_telemetry(enabled=True, service_version="probe")
    with telemetry.operation("ai.chat"):
      result = 42
      telemetry.emit_event("ai.finished", {})
      telemetry.record_ai_usage("chat", 1, None)
    started = time.monotonic()
    await telemetry.close_telemetry()
    refused_close = time.monotonic() - started
  assert result == 42 and refused_close < 5
  for signal in ("TRACES", "LOGS", "METRICS"):
    os.environ[f"OTEL_EXPORTER_OTLP_{signal}_ENDPOINT"] = (
      f"{endpoint}/slow/{signal.lower()}"
    )
  delay = 2.0
  before = len(records)
  with redirect_stderr(diagnostic):
    telemetry.start_telemetry(enabled=True, service_version="probe")
    started = time.monotonic()
    for _ in range(1024):
      with telemetry.operation("ai.chat"):
        telemetry.emit_event("ai.finished", {})
        telemetry.record_ai_usage("chat", 1, 1)
    operation_elapsed = time.monotonic() - started
    started = time.monotonic()
    await telemetry.close_telemetry()
    slow_close = time.monotonic() - started
  assert operation_elapsed < 1, operation_elapsed
  assert slow_close < 5, slow_close
  assert not telemetry.is_enabled() and len(records) > before
  assert CANARY not in diagnostic.getvalue()
  pipeline = []
  dropped = {}
  export_failures = {}
  for path, body, _ in records[before:]:
    if not path.endswith("metrics"):
      continue
    batch = ExportMetricsServiceRequest.FromString(body)
    for resource in batch.resource_metrics:
      for scope in resource.scope_metrics:
        if scope.scope.name != "opentelemetry-sdk":
          continue
        for metric in scope.metrics:
          pipeline.append(metric.name)
          data = getattr(metric, metric.WhichOneof("data"))
          for point in data.data_points:
            attrs = {attr.key: attr.value for attr in point.attributes}
            assert set(attrs) <= {
              "otel.component.type",
              "error.type",
              "http.response.status_code",
            }
            assert not point.exemplars
            if attrs.get("error.type") and attrs["error.type"].string_value == "queue_full":
              dropped[metric.name] = dropped.get(metric.name, 0) + point.as_int
            if (
              metric.name.startswith("otel.sdk.exporter.")
              and metric.name.endswith(".exported")
              and attrs.get("error.type")
            ):
              export_failures[metric.name] = (
                export_failures.get(metric.name, 0) + point.as_int
              )
  assert dropped.get("otel.sdk.processor.span.processed", 0) > 0, dropped
  assert dropped.get("otel.sdk.processor.log.processed", 0) > 0, dropped
  assert export_failures.get("otel.sdk.exporter.span.exported", 0) > 0, export_failures
  assert export_failures.get("otel.sdk.exporter.log.exported", 0) > 0, export_failures
  assert "otel.sdk.exporter.operation.duration" in pipeline, pipeline
  assert "otel.sdk.processor.span.queue.capacity" in pipeline
  assert "otel.sdk.processor.log.queue.size" in pipeline
  delay = 0
  fault_checks = await injected_faults(endpoint, diagnostic)
  timeout_checks = await timeout_configuration(endpoint, diagnostic)
  server.shutdown()
  server.server_close()
  evidence = {
    "off_no_threads_or_exports": True,
    "three_signals": True,
    "canary_absent": True,
    "usage_known_zero_missing": True,
    "exception_and_cancellation_propagate": True,
    "restart": True,
    "invalid_configuration_isolated": True,
    "healthy_shutdown_seconds": healthy_close,
    "slow_receiver_backlog_shutdown_seconds": slow_close,
    "refused_receiver_shutdown_seconds": refused_close,
    "backlog_business_seconds": operation_elapsed,
    "requests": len(records),
    "native_pipeline_metric_names": sorted(set(pipeline)),
    "native_queue_drops": dropped,
    "native_export_failures": export_failures,
    "native_metric_attributes_and_exemplars_safe": True,
    "fault_injection_checks": fault_checks,
    "timeout_configuration": timeout_checks,
  }
  destination = Path(__file__).parent / "evidence" / "foundation-probe.json"
  destination.write_text(json.dumps(evidence, indent=2) + "\n")
  print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
  asyncio.run(main())
