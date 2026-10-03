"""Inspect local OTLP protobuf capture using the official generated message classes."""

import base64
import json
import sys
from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import (
  ExportMetricsServiceRequest,
)
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
  ExportTraceServiceRequest,
)

models = {
  "/v1/traces": ExportTraceServiceRequest,
  "/v1/logs": ExportLogsServiceRequest,
  "/v1/metrics": ExportMetricsServiceRequest,
}


def inspect(value):
  if isinstance(value, list):
    return [inspect(item) for item in value]
  if isinstance(value, dict):
    return {
      key: base64.b64decode(item).hex()
      if key in {"traceId", "spanId", "parentSpanId"}
      else inspect(item)
      for key, item in value.items()
    }
  return value


records = json.load(sys.stdin)
for record in records:
  model = models[record["signal"]].FromString(base64.b64decode(record["data"]))
  record["data"] = inspect(MessageToDict(model))
json.dump(records, sys.stdout)
