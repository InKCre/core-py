"""Verify synthetic browser batches captured beyond the real core OTLP relay."""

import json
from pathlib import Path
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import (
  ExportMetricsServiceRequest,
)
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
  ExportTraceServiceRequest,
)

here = Path(__file__).resolve().parent
report_path = here / "client-real-relay-result.json"
report = json.loads(report_path.read_text())
records = json.loads((here / "runtime/browser-real-relay.json").read_text())
models = {
  "/v1/traces": (ExportTraceServiceRequest, "resource_spans"),
  "/v1/logs": (ExportLogsServiceRequest, "resource_logs"),
  "/v1/metrics": (ExportMetricsServiceRequest, "resource_metrics"),
}
matched = {key: 0 for key in models}
trace_ids = set()
span_ids = {}
execution_links = []
events = set()
event_contexts = {}
metric_names = set()
for record in records:
  definition = models.get(record["path"])
  if definition is None:
    continue
  model, field = definition
  payload = model.FromString(bytes.fromhex(record["body_hex"]))
  for resource in getattr(payload, field):
    attributes = {
      item.key: item.value.string_value for item in resource.resource.attributes
    }
    if attributes.get("service.version") != report["version"]:
      continue
    assert attributes["service.name"] == "inkcre.client-web"
    assert attributes["inkcre.peer.id"] == "00000000-0000-4000-8000-000000000001"
    assert attributes["inkcre.deployment.id"]
    assert attributes["service.instance.id"]
    assert record["server_auth_ok"], (
      "upstream must receive only server-managed ingest authentication"
    )
    matched[record["path"]] += 1
    if field == "resource_spans":
      for scope in resource.scope_spans:
        for span in scope.spans:
          trace_ids.add(span.trace_id.hex())
          span_ids[span.name] = (span.trace_id.hex(), span.span_id.hex())
          if span.name == "job.execute":
            assert not span.parent_span_id
            execution_links.extend(
              (link.trace_id.hex(), link.span_id.hex()) for link in span.links
            )
            assert all(link.flags & 1 == 1 for link in span.links)
    elif field == "resource_logs":
      for scope in resource.scope_logs:
        for log in scope.log_records:
          events.add(log.body.string_value)
          if log.body.string_value in {"job.submitted", "job.started"}:
            event_contexts[log.body.string_value] = (log.trace_id.hex(), log.span_id.hex())
            assert any(
              item.key == "inkcre.job.id" and item.value.int_value == 900001
              for item in log.attributes
            )
    elif field == "resource_metrics":
      for scope in resource.scope_metrics:
        for metric in scope.metrics:
          metric_names.add(metric.name)
          if metric.name == "inkcre.operation.duration":
            assert metric.unit == "s"
            for point in metric.histogram.data_points:
              assert {item.key for item in point.attributes} == {
                "inkcre.operation",
                "inkcre.outcome",
              }
assert all(matched.values()), matched
assert span_ids["job.submit"] == (report["traceId"], report["spanId"])
assert span_ids["job.execute"] == (report["executionTraceId"], report["executionSpanId"])
assert report["executionTraceId"] != report["traceId"]
assert execution_links == [(report["traceId"], report["spanId"])]
assert event_contexts["job.submitted"] == (report["traceId"], report["spanId"])
assert event_contexts["job.started"] == (
  report["executionTraceId"],
  report["executionSpanId"],
)
assert "inkcre.operation.duration" in metric_names
report.update(
  upstreamVerified=True,
  upstreamBrowserResources=matched,
  upstreamServerAuthentication=True,
  relayEncoding="OTLP/protobuf → OTLP/protobuf",
  exactTraceSpanIdsAndLinkPreserved=True,
  correlatedJobEventsAndBoundedMetricLabels=True,
)
report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
print(
  json.dumps(
    {
      key: report[key]
      for key in (
        "upstreamVerified",
        "upstreamBrowserResources",
        "upstreamServerAuthentication",
        "relayEncoding",
        "exactTraceSpanIdsAndLinkPreserved",
      )
    },
    ensure_ascii=False,
  )
)
