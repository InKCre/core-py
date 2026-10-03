# /// script
# requires-python = ">=3.12"
# dependencies = ["opentelemetry-sdk==1.45.0"]
# ///
"""Prove SDK normalization and the need for an application-owned persistence size
boundary."""

import json
from pathlib import Path

from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags, TraceState
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

propagator = TraceContextTextMapPropagator()
state = TraceState([(f"v{i}", "s" * 30) for i in range(32)])
source = SpanContext(1, 2, False, TraceFlags(1), state)
carrier = {}
propagator.inject(carrier, trace.set_span_in_context(NonRecordingSpan(source), Context()))
assert len(carrier["traceparent"]) == 55
assert len(carrier["tracestate"].encode()) > 512
# Candidate boundary policy: keep traceparent, omit oversized optional state as a whole.
# It does not parse W3C, truncate inside an entry, or fail the business create transaction.
bounded = {key: value for key, value in carrier.items() if len(value.encode()) <= 512}
restored = trace.get_current_span(propagator.extract(bounded, Context())).get_span_context()
assert (restored.trace_id, restored.span_id, restored.trace_flags) == (
  source.trace_id,
  source.span_id,
  source.trace_flags,
)
assert not restored.trace_state
future = {"traceparent": "01" + carrier["traceparent"][2:] + "-extension"}
normalized = {}
propagator.inject(normalized, propagator.extract(future, Context()))
assert normalized["traceparent"] == carrier["traceparent"]
report = {
  "sdk_injected_traceparent_bytes": 55,
  "sdk_injected_tracestate_bytes": len(carrier["tracestate"].encode()),
  "candidate_max_bytes_each": 512,
  "oversize_state_policy": "omit optional state as a whole; preserve parent IDs/flags",
  "future_context_reinjected_as_version_00": True,
  "persistence_limit_is_application_policy_not_W3C_maximum": True,
}
(Path(__file__).parent / "runtime/carrier-capacity.json").write_text(
  json.dumps(report, indent=2) + "\n"
)
print(json.dumps(report, indent=2))
