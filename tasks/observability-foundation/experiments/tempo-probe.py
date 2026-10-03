"""Reuse the OpenObserve discriminator sample; query before and after a separate restart."""

import base64
import json
from pathlib import Path
import sys
import time
import urllib.request
import urllib.parse

HERE = Path(__file__).resolve().parent


def read_trace(trace_id):
  request = urllib.request.Request(
    "http://127.0.0.1:33200/api/v2/traces/" + trace_id,
    headers={"Accept": "application/json"},
  )
  with urllib.request.urlopen(request, timeout=20) as response:
    return json.load(response)


def attributes(items):
  return {item["key"]: item["value"] for item in items}


def compare(expected, response):
  spans = [
    span
    for resource in response["trace"].get("resourceSpans", [])
    for scope in resource.get("scopeSpans", [])
    for span in scope.get("spans", [])
  ]
  assert len(spans) == 1, (expected["name"], response)
  actual = spans[0]
  assert actual["name"] == expected["name"]
  # Tempo's query JSON uses protobuf base64 bytes for IDs; OTLP/HTTP JSON uses hex.
  for field in ["traceId", "spanId"]:
    assert actual[field] == base64.b64encode(bytes.fromhex(expected[field])).decode()
  for field in ["startTimeUnixNano", "endTimeUnixNano"]:
    assert actual[field] == expected[field]
  assert attributes(actual["attributes"]) == attributes(expected["attributes"])
  assert len(actual.get("links", [])) == len(expected.get("links", []))
  flags_preserved = True
  for original, stored in zip(
    expected.get("links", []), actual.get("links", []), strict=True
  ):
    for field in ["traceId", "spanId"]:
      assert stored[field] == base64.b64encode(bytes.fromhex(original[field])).decode()
    assert stored["traceState"] == original["traceState"]
    assert attributes(stored["attributes"]) == attributes(original["attributes"])
    flags_preserved &= stored.get("flags", 0) == original.get("flags", 0)
  return flags_preserved


def main(action):
  input_path = HERE / "runtime/tempo-input.json"
  if action == "send":
    payload = json.loads(
      (HERE / "evidence/openobserve-20261001/ai-projection.json").read_text()
    )["input"]
    now = time.time_ns()
    for span in payload["resourceSpans"][0]["scopeSpans"][0]["spans"]:
      span["startTimeUnixNano"] = str(now)
      span["endTimeUnixNano"] = str(now + 1000)
      span["attributes"].append({"key": "inkcre.job.id", "value": {"intValue": "42"}})
    input_path.write_text(json.dumps(payload, indent=2) + "\n")
    request = urllib.request.Request(
      "http://127.0.0.1:34318/v1/traces",
      data=json.dumps(payload).encode(),
      headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
      assert response.status == 200
    print("Synthetic sample accepted by Collector; backend readback pending")
  elif action in {"before", "after"}:
    payload = json.loads(input_path.read_text())
    spans = payload["resourceSpans"][0]["scopeSpans"][0]["spans"]
    output = {span["name"]: read_trace(span["traceId"]) for span in spans}
    (HERE / f"runtime/tempo-{action}.json").write_text(json.dumps(output, indent=2) + "\n")
    flags = [compare(span, output[span["name"]]) for span in spans]
    params = urllib.parse.urlencode(
      {
        "q": "{ span.inkcre.job.id = 42 }",
        "start": int(time.time() - 3600),
        "end": int(time.time() + 60),
      }
    )
    with urllib.request.urlopen(
      "http://127.0.0.1:33200/api/search?" + params, timeout=20
    ) as response:
      search = json.load(response)
    assert {row["traceID"] for row in search["traces"]} == {
      span["traceId"] for span in spans
    }
    (HERE / f"runtime/tempo-search-{action}.json").write_text(
      json.dumps(search, indent=2) + "\n"
    )
    print(
      json.dumps(
        {
          "phase": action,
          "traces_found_by_job": len(search["traces"]),
          "attribute_presence_types_and_values": "passed",
          "link_ids_state_attributes": "passed",
          "link_flags_preserved": all(flags),
        },
        indent=2,
      )
    )
  else:
    raise SystemExit("Use send, before, or after")


if __name__ == "__main__":
  main(sys.argv[1])
