import os
import sys
import json
import time
import subprocess
from pathlib import Path

import httpx
import jwt
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
os.environ.update(
  DATABASE_URL="postgresql+psycopg://localhost/unused",
  JWT_SECRET="unused-local-placeholder-at-least-32-bytes",
  INKCRE_ENV_FILE="",
)
from tests.organization.acceptance.test_black_box import _BEHAVIORS, _READ_TOOLS
from tests.organization.acceptance.corpus import load_manifest, read_artifact

PG = "https://inkcre-postgrest-pr-100-b493a9d718a7.herokuapp.com"
CORE = "https://inkcre-core-py-pr-100-daaa8aaa5621.herokuapp.com"
MODE = sys.argv[1]
if MODE not in ("baseline", "repaired"):
  raise ValueError("Choose baseline or repaired")
OUT = Path(__file__).with_name(f"tool-repair-{MODE}.json")
if OUT.exists():
  raise RuntimeError("Evidence already exists; do not overwrite a prior run")
SAVED = json.loads(Path(__file__).with_name("preview-100-deployment.json").read_text())
secret = subprocess.check_output(
  ["security", "find-generic-password", "-s", "inkcre/core-py/JWT_SECRET", "-w"], text=True
).strip()
client = httpx.Client(timeout=60)


def call(method, path, data=None, core=False):
  now = int(time.time())
  token = jwt.encode(
    dict(role="authenticated", iss="inkcre-peer", aud="inkcre-api", iat=now, exp=now + 600),
    secret,
    algorithm="HS256",
  )
  r = client.request(
    method,
    (CORE if core else PG) + path,
    json=data,
    headers={"Authorization": "Bearer " + token, "Prefer": "return=representation"},
  )
  if r.is_error:
    raise RuntimeError(
      f"{method} {path.split('?')[0]} HTTP {r.status_code}: {r.text[:300]}"
    )
  return r.json() if r.content else None


def ids(table):
  return {row["id"] for row in call("GET", f"/{table}?select=id&limit=10000")}


def insert(table, data):
  return call("POST", "/" + table, data)[0]["id"]


evidence = {
  "head": subprocess.check_output(
    ["gh", "pr", "view", "100", "--json", "headRefOid", "--jq", ".headRefOid"], text=True
  ).strip(),
  "mode": MODE,
  "model": "qwen3.6-plus",
  "rounds": [],
  "cleanup": {},
}
baseline = {
  table: ids(table)
  for table in ("blocks", "relations", "jobs", "agents", "ai_models", "ai_providers")
}
if baseline["blocks"] or baseline["agents"] or baseline["ai_providers"]:
  raise RuntimeError(
    "Preview contains existing information/Agents/providers; requires isolation"
  )
if call("GET", "/jobs?status=in.(pending,running)&select=id"):
  raise RuntimeError("Existing active Jobs")
configs = call("GET", "/configs")
backups = {r["key"]: r for r in configs}
configured = []
aliases = {}


def snapshot():
  return {
    table: call("GET", f"/{table}?order=id&limit=10000")
    for table in ("blocks", "relations")
  }


def job(type_, parameters):
  ident = insert("jobs", dict(type=type_, parameters=parameters, timeout_seconds=900))
  started = time.monotonic()
  while time.monotonic() - started < 1000:
    row = call("GET", f"/jobs?id=eq.{ident}")[0]
    if row["status"] not in ("pending", "running"):
      print("JOB", ident, type_, row["status"], flush=True)
      return row
    time.sleep(5)
  raise TimeoutError(f"Job {ident} remains active")


try:
  values = dotenv_values(ROOT / ".env")
  provider = insert(
    "ai_providers",
    dict(
      name="PR100 Organization acceptance",
      dialect="core.openai-compatible.v1",
      config=dict(api_key=values["LLM_SP_AK"], base_url=values["LLM_SP_BASE_URL"]),
    ),
  )
  model = insert(
    "ai_models",
    dict(
      provider=provider,
      native_model_id="qwen3.6-plus",
      capabilities=[
        dict(
          type="chat",
          input_modalities=["text"],
          output_modalities=["text"],
          features=["tool_calling"],
        )
      ],
    ),
  )
  for b in _BEHAVIORS:
    saved = next(a for a in SAVED["agents"] if a["name"] == "PR100 acceptance " + b.name)
    tools = (
      saved["tools"]
      if MODE == "baseline"
      else sorted(set(_READ_TOOLS + b.mutation_tools + ("record_organization_candidate",)))
    )
    agent = insert(
      "agents",
      dict(
        name="PR100 tool repair " + b.name,
        model=model,
        tools=tools,
        tool_choice="auto",
        max_model_calls_per_turn=12,
        system_prompt=saved["system_prompt"],
      ),
    )
    configured.append(b.config_key)
    call(
      "PUT",
      "/configs/" + b.config_key,
      {"schema": b.config_schema, "value": {"agent": agent}},
      core=True,
    )
  manifest = load_manifest()
  for world in manifest.worlds:
    for artifact in world.artifacts:
      aliases[artifact.alias] = insert(
        "blocks", dict(resolver="core.text.v1", content=read_artifact(artifact.path))
      )
    for relation in world.relations:
      insert(
        "relations",
        {
          "from_": aliases[relation.from_],
          "to_": aliases[relation.to],
          "content": relation.content,
        },
      )
  evidence["aliases"] = aliases
  evidence["before"] = snapshot()
  evidence["definitions"] = call("GET", "/agents")
  OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
  for n in (1,):
    if n == 2:
      change = manifest.upstream_change
      aliases[change.alias] = insert(
        "blocks", dict(resolver="core.text.v1", content=read_artifact(change.path))
      )
      insert(
        "relations",
        {
          "from_": aliases[change.predecessor],
          "to_": aliases[change.alias],
          "content": change.relation,
        },
      )
    stage = {"round": n, "jobs": []}
    evidence["rounds"].append(stage)
    stage["maintenance"] = job(
      "core.feature_retrieval.lexical.maintain.v1", {"options": {"max_records": 10000}}
    )
    for b in _BEHAVIORS:
      completed = job(b.job_type, {"max_seeds": 3})
      logs = call(
        "GET", f"/logs?trace_id=eq.job.{completed['id']}&order=id.asc&limit=10000"
      )
      stage["jobs"].append(
        {
          "job": completed,
          "events": [
            json.loads(r["body"])
            for r in logs
            if r.get("attributes", {}).get("agent_thread_id")
          ],
        }
      )
      OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
    stage["graph"] = snapshot()
    print(
      "ROUND",
      n,
      "blocks",
      len(stage["graph"]["blocks"]),
      "relations",
      len(stage["graph"]["relations"]),
      flush=True,
    )
except Exception as error:
  evidence["failure"] = str(error)
  print("FAILURE", str(error), flush=True)
finally:
  # Only delete this run's IDs, after all its Jobs have stopped.
  active = call("GET", "/jobs?status=in.(pending,running)&select=id")
  if active:
    evidence["cleanup"]["deferred_active_jobs"] = [r["id"] for r in active]
  else:
    for key in configured:
      if key in backups:
        row = backups[key]
        call(
          "PUT",
          "/configs/" + key,
          {"schema": row["schema"], "value": row["value"]},
          core=True,
        )
      else:
        call("DELETE", "/configs", None) if False else call(
          "DELETE", "/configs?key=eq." + key
        )
    for stage in evidence["rounds"]:
      for item in stage["jobs"]:
        call("DELETE", f"/logs?trace_id=eq.job.{item['job']['id']}")
    for table in ("relations", "blocks", "jobs", "agents", "ai_models", "ai_providers"):
      created = ids(table) - baseline[table]
      for start in range(0, len(created), 100):
        chunk = sorted(created)[start : start + 100]
        call("DELETE", "/" + table + "?id=in.(" + ",".join(map(str, chunk)) + ")")
      evidence["cleanup"][table] = {
        "removed": len(created),
        "remaining_new_ids": sorted(ids(table) - baseline[table]),
      }
  OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
  print("EVIDENCE", OUT, flush=True)
