"""Discriminate absent/zero/explicit source facts and linked-span export retention."""

import json
from pathlib import Path
import time
import urllib.request
import uuid

from readback import query


def attrs(values):
  return [
    {
      "key": key,
      "value": {"intValue": str(value)}
      if type(value) is int
      else {"doubleValue": value}
      if type(value) is float
      else {"stringValue": value},
    }
    for key, value in values.items()
  ]


def main():
  run_id = uuid.uuid4().hex
  parent_trace, parent_span = uuid.uuid4().hex, uuid.uuid4().hex[:16]
  now = time.time_ns()
  cases = {
    "absent": {},
    "explicit": {
      "gen_ai.agent.version": "agent-7",
      "gen_ai.usage.input_tokens": 8,
      "gen_ai.usage.output_tokens": 3,
      "gen_ai.usage.cost": 0.125,
    },
    "zero": {
      "gen_ai.usage.input_tokens": 0,
      "gen_ai.usage.output_tokens": 0,
      "gen_ai.usage.cost": 0.0,
    },
  }
  spans = [
    {
      "name": "submission",
      "traceId": parent_trace,
      "spanId": parent_span,
      "startTimeUnixNano": str(now),
      "endTimeUnixNano": str(now + 1000),
      "attributes": attrs({"inkcre.lab.run_id": run_id}),
    }
  ]
  for name, fields in cases.items():
    spans.append(
      {
        "name": name,
        "traceId": uuid.uuid4().hex,
        "spanId": uuid.uuid4().hex[:16],
        "startTimeUnixNano": str(now),
        "endTimeUnixNano": str(now + 1000),
        "attributes": attrs(
          {
            "inkcre.lab.run_id": run_id,
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "synthetic",
            **fields,
          }
        ),
        "links": [
          {
            "traceId": parent_trace,
            "spanId": parent_span,
            "traceState": "inkcre=synthetic",
            "flags": 1,
            "attributes": attrs(
              {"inkcre.link.reason": "job-submission", "inkcre.link.sequence": 7}
            ),
          }
        ],
      }
    )
  payload = {
    "resourceSpans": [
      {
        "resource": {
          "attributes": attrs(
            {"service.name": "inkcre-projection-probe", "service.version": "service-3"}
          )
        },
        "scopeSpans": [{"spans": spans}],
      }
    ]
  }
  request = urllib.request.Request(
    "http://127.0.0.1:34318/v1/traces",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
  )
  with urllib.request.urlopen(request, timeout=5) as response:
    assert response.status == 200
  time.sleep(3)
  result = query(f"SELECT * FROM default WHERE inkcre_lab_run_id = '{run_id}'", "traces")
  (Path(__file__).parent / "runtime/ai-projection.json").write_text(
    json.dumps({"input": payload, "output": result}, indent=2) + "\n"
  )
  rows = {row["operation_name"]: row for row in result["hits"]}
  assert set(rows) == {*cases, "submission"}
  explicit = rows["explicit"]
  assert explicit["gen_ai_agent_version"] == "agent-7"
  assert explicit["gen_ai_usage_cost"] == 0.125
  for key, value in {
    "gen_ai_usage_input_tokens": 8,
    "gen_ai_usage_output_tokens": 3,
  }.items():
    assert explicit[key] == value
  links = {name: json.loads(rows[name]["links"])[0] for name in cases}
  for link in links.values():
    assert link["context"]["traceId"] == parent_trace
    assert link["context"]["spanId"] == parent_span
    assert link["context"]["traceState"] == "inkcre=synthetic"
    # OpenObserve's SpanLink projection flattens attributes into the link object.
    assert link["inkcre.link.reason"] == "job-submission"
    assert link["inkcre.link.sequence"] == "7"  # Numeric custom attributes are stringified.
  parent = query(
    f"SELECT * FROM default WHERE trace_id = '{parent_trace}' AND span_id = '{parent_span}'",  # noqa: E501
    "traces",
  )
  assert parent["hits"][0]["operation_name"] == "submission"
  (Path(__file__).parent / "runtime/ai-projection.json").write_text(
    json.dumps({"input": payload, "output": result, "linked_submission": parent}, indent=2)
    + "\n"
  )
  keys = [
    "gen_ai_agent_version",
    "gen_ai_usage_input_tokens",
    "gen_ai_usage_output_tokens",
    "gen_ai_usage_cost",
  ]
  print(
    json.dumps(
      {
        "explicit_fields_preserved": True,
        "link_attributes_and_state_exported": True,
        "link_attribute_type_preserved": all(
          type(link["inkcre.link.sequence"]) is int for link in links.values()
        ),
        "missing_usage_remains_unknown": all(
          key not in rows["absent"]
          for key in [
            "gen_ai_usage_input_tokens",
            "gen_ai_usage_output_tokens",
            "gen_ai_usage_cost",
          ]
        ),
        "missing_agent_version_remains_absent": "gen_ai_agent_version"
        not in rows["absent"],
        "absence_vs_zero": {
          name: {key: rows[name].get(key) for key in keys} for name in cases
        },
      },
      indent=2,
    )
  )


if __name__ == "__main__":
  main()
