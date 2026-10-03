"""Run through the core-py PDM environment against its unchanged current schema."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.schemas.job import JobCreateForm, JobModel
from pydantic import ValidationError

base = dict(
  id=42,
  type="synthetic",
  parameters={},
  state={},
  timeout_seconds=30,
  status="pending",
  created_at="2026-10-01T00:00:00Z",
)
for carrier in [
  {},
  {"submission_traceparent": None, "submission_tracestate": None},
  {
    "submission_traceparent": "00-" + "1" * 32 + "-" + "2" * 16 + "-01",
    "submission_tracestate": "inkcre=synthetic",
  },
]:
  job = JobModel.model_validate({**base, **carrier})
  assert job.id == 42 and job.status == "pending"
  assert "submission_traceparent" not in job.model_dump()
try:
  JobCreateForm.model_validate({"type": "synthetic", "submission_traceparent": "synthetic"})
except ValidationError:
  pass
else:
  raise AssertionError("Old REST creation input unexpectedly admits telemetry fields")
print(
  json.dumps(
    {
      "actual_legacy_python_schema": "accepted missing, NULL and additional carrier fields; unknown fields ignored",  # noqa: E501
      "old_rest_create_form": "rejects extra carrier fields; use HTTP propagation at the transport boundary",  # noqa: E501
      "database_updates": "not exercised",
    },
    indent=2,
  )
)
