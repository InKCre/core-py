"""Send a bounded synthetic run using the real facade and private local OTLP config."""

import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import uuid

import certifi
import urllib3
from opentelemetry.context import Context
from opentelemetry.trace import Link

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
os.environ["INKCRE_ENV_FILE"] = str(ROOT / ".env")
# This workstation Python has no system CA path; keep TLS verification enabled.
os.environ.setdefault("OTEL_EXPORTER_OTLP_CERTIFICATE", certifi.where())

from libs.obsrv.telemetry import (
  close_telemetry,
  emit_event,
  is_enabled,
  operation,
  record_ai_usage,
  start_telemetry,
)

run_id = str(uuid.uuid4())
responses = []
original_request = urllib3.PoolManager.request


def observed_request(pool, method, url, **kwargs):
  """Observe only status/protocol counters; send the original real network request."""
  signal = url.rsplit("/", 1)[-1]
  try:
    response = original_request(pool, method, url, **kwargs)
  except Exception as error:
    responses.append(
      {
        "signal": signal,
        "transport_error": type(error).__name__,
        "reason_type": type(getattr(error, "reason", None)).__name__,
      }
    )
    raise
  responses.append({"signal": signal, "status": response.status})
  return response


urllib3.PoolManager.request = observed_request
report = {"run_id": run_id, "started_at": datetime.now(timezone.utc).isoformat()}
try:
  start_telemetry(
    enabled=True,
    service_version="observability-acceptance",
    resource_attributes={
      "inkcre.deployment.id": run_id,
      "inkcre.peer.id": "00000000-0000-4000-8000-000000000099",
      "inkcre.acceptance.synthetic": True,
    },
  )
  assert is_enabled(), "No configured signal initialized"
  with operation("job.submit", attributes={"inkcre.job.id": 900001}) as submitted:
    submit_context = submitted.span.get_span_context()
    emit_event("job.submitted", {"inkcre.job.id": 900001})
  with operation(
    "job.execute",
    context=Context(),
    links=(Link(submit_context),),
    attributes={"inkcre.job.id": 900001},
  ) as executed:
    report["submit_trace_id"] = format(submit_context.trace_id, "032x")
    report["execute_trace_id"] = format(executed.span.get_span_context().trace_id, "032x")
    with operation(
      "ai.chat",
      attributes={
        "inkcre.ai.usage.input.source": "provider",
        "gen_ai.usage.input_tokens": 0,
        "inkcre.ai.usage.output.source": "unavailable",
      },
    ):
      record_ai_usage("ai.chat", input_tokens=0, output_tokens=None)
    emit_event("job.closed", {"inkcre.job.id": 900001, "outcome": "success"})
finally:
  asyncio.run(close_telemetry())
  urllib3.PoolManager.request = original_request
report["http_responses"] = responses
report["all_signals_accepted"] = all(
  any(item.get("signal") == name and item.get("status") in (200, 204) for item in responses)
  for name in ("traces", "logs", "metrics")
)
report["query_verified"] = False
target = Path(__file__).parent / "evidence/cloud-probe.json"
target.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
