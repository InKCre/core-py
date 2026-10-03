# /// script
# requires-python = ">=3.12"
# dependencies = ["opentelemetry-sdk==1.45.0"]
# ///
"""Run with pdm run propagation.py; no application or dependency-file changes."""

import asyncio
import io
import json
import logging
from pathlib import Path
import subprocess

from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


async def main():
  diagnostic = io.StringIO()
  diagnostic_handler = logging.StreamHandler(diagnostic)
  sdk_logger = logging.getLogger("opentelemetry.trace.span")
  sdk_logger.addHandler(diagnostic_handler)
  exporter = InMemorySpanExporter()
  provider = TracerProvider()
  provider.add_span_processor(SimpleSpanProcessor(exporter))
  tracer = provider.get_tracer("contract-probe")
  propagator = TraceContextTextMapPropagator()
  with tracer.start_as_current_span("python-submit", context=Context()):
    carrier = {}
    propagator.inject(carrier)
  carrier["tracestate"] = "inkcre=synthetic"
  parent = carrier["traceparent"]
  vectors = [
    {"name": "sampled", "carrier": carrier, "valid": True},
    {"name": "unsampled", "carrier": {"traceparent": parent[:-2] + "00"}, "valid": True},
    {
      "name": "future-version",
      "carrier": {"traceparent": "01" + parent[2:] + "-extra"},
      "valid": True,
    },
    {"name": "missing", "carrier": {}, "valid": False},
    {"name": "malformed", "carrier": {"traceparent": "broken"}, "valid": False},
    {
      "name": "zero-id",
      "carrier": {"traceparent": "00-" + "0" * 32 + "-" + "1" * 16 + "-01"},
      "valid": False,
    },
    {
      "name": "bad-state",
      "carrier": {"traceparent": parent, "tracestate": "o11y-sensitive-canary"},
      "valid": True,
    },
  ]
  js = json.loads(
    subprocess.check_output(  # noqa: S603
      ["node", str(Path(__file__).with_suffix(".mjs"))],
      input=json.dumps(vectors),
      text=True,
    )
  )
  for vector, result in zip(vectors, js, strict=True):
    extracted = trace.get_current_span(
      propagator.extract(vector["carrier"], Context())
    ).get_span_context()
    assert extracted.is_valid == vector["valid"], vector["name"]
    restored = trace.get_current_span(
      propagator.extract(result["roundtrip"], Context())
    ).get_span_context()
    assert (restored.trace_id, restored.span_id, restored.trace_flags) == (
      extracted.trace_id,
      extracted.span_id,
      extracted.trace_flags,
    )
    assert dict(restored.trace_state) == dict(extracted.trace_state)

  async def receive(result):
    linked_context = trace.get_current_span(
      propagator.extract(result["outgoing"], Context())
    ).get_span_context()
    assert linked_context.is_valid
    with tracer.start_as_current_span(
      result["name"], context=Context(), links=[trace.Link(linked_context)]
    ) as span:
      await asyncio.sleep(0)
      assert trace.get_current_span() is span
      assert span.get_span_context().trace_id != linked_context.trace_id
      return span.get_span_context().trace_id

  ids = await asyncio.gather(*(receive(result) for result in js))
  assert len(set(ids)) == len(js)
  spans = exporter.get_finished_spans()[1:]
  assert all(span.parent is None and len(span.links) == 1 for span in spans)
  provider.shutdown()
  sdk_logger.removeHandler(diagnostic_handler)
  result = {
    "vectors": [v["name"] for v in vectors],
    "python_to_js_to_python": "passed",
    "independent_execution_links": "passed",
    "python_async_context_isolation": "passed",
    "js_explicit_context_isolation": "passed",
    "sdk_invalid_state_diagnostic_contains_raw_value": "o11y-sensitive-canary"
    in diagnostic.getvalue(),
    "browser_runtime": "not tested",
  }
  (Path(__file__).parent / "runtime" / "propagation.json").write_text(
    json.dumps(result, indent=2) + "\n"
  )
  print(json.dumps(result, indent=2))


if __name__ == "__main__":
  asyncio.run(main())
