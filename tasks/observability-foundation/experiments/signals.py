# /// script
# requires-python = ">=3.12"
# dependencies = ["opentelemetry-sdk==1.45.0", "opentelemetry-exporter-otlp-proto-
# http==1.45.0"]
# ///
"""Send one synthetic causal chain, a correlated log, counter and histogram."""

import json
from pathlib import Path
import uuid

from opentelemetry import trace
from opentelemetry._logs import SeverityNumber
from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import SimpleLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.metrics.view import ExplicitBucketHistogramAggregation, View
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


def main():
  run_id = uuid.uuid4().hex
  endpoint = "http://127.0.0.1:34318/v1/"
  resource = Resource.create(
    {
      "service.name": "inkcre-o11y-synthetic",
      "service.version": "g1",
      "inkcre.deployment.id": "synthetic-g1",
      "inkcre.peer.id": "synthetic-python",
    }
  )
  traces = TracerProvider(resource=resource)
  traces.add_span_processor(
    SimpleSpanProcessor(OTLPSpanExporter(endpoint=endpoint + "traces", timeout=3))
  )
  logs = LoggerProvider(resource=resource)
  logs.add_log_record_processor(
    SimpleLogRecordProcessor(OTLPLogExporter(endpoint=endpoint + "logs", timeout=3))
  )
  metrics = MeterProvider(
    resource=resource,
    metric_readers=[
      PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=endpoint + "metrics", timeout=3),
        export_interval_millis=3600000,
      )
    ],
    views=[
      View(
        instrument_name="inkcre_lab_duration",
        aggregation=ExplicitBucketHistogramAggregation([0.1, 0.25, 0.5]),
      )
    ],
  )
  tracer = traces.get_tracer("inkcre-g1")
  attributes = {"inkcre.job.id": 42, "inkcre.lab.run_id": run_id}
  with tracer.start_as_current_span(
    "job.submit", context=Context(), attributes=attributes
  ) as submit:
    submitted = submit.get_span_context()
  with tracer.start_as_current_span(
    "job.execute", context=Context(), links=[trace.Link(submitted)], attributes=attributes
  ) as job:
    executed = job.get_span_context()
    with tracer.start_as_current_span(
      "chat synthetic-model",
      attributes={
        **attributes,
        "gen_ai.operation.name": "chat",
        "gen_ai.provider.name": "synthetic",
        "gen_ai.usage.input_tokens": 8,
        "gen_ai.usage.output_tokens": 3,
        "gen_ai.response.finish_reasons": ["stop"],
      },
    ):
      pass
    logs.get_logger("inkcre-g1").emit(
      body="synthetic job finished",
      severity_number=SeverityNumber.INFO,
      attributes=attributes,
    )
  meter = metrics.get_meter("inkcre-g1")
  meter.create_counter("inkcre_lab_jobs", unit="{job}").add(3, {"outcome": "finished"})
  duration = meter.create_histogram("inkcre_lab_duration", unit="s")
  for value in [0.1, 0.3]:
    duration.record(value, {"operation": "synthetic"})
  metrics.force_flush()
  traces.force_flush()
  logs.force_flush()
  metrics.shutdown()
  traces.shutdown()
  logs.shutdown()
  result = {
    "run_id": run_id,
    "submission_trace_id": format(submitted.trace_id, "032x"),
    "submission_span_id": format(submitted.span_id, "016x"),
    "execution_trace_id": format(executed.trace_id, "032x"),
    "execution_span_id": format(executed.span_id, "016x"),
    "expected_job_counter": 3,
    "expected_duration_count": 2,
    "expected_duration_sum": 0.4,
  }
  (Path(__file__).parent / "runtime" / "expected.json").write_text(
    json.dumps(result, indent=2) + "\n"
  )
  print(json.dumps(result, indent=2))


if __name__ == "__main__":
  main()
