import os
import sys
import json
import time
import subprocess
from datetime import datetime
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
if MODE not in (
  "baseline",
  "repaired",
  "prompt",
  "batch",
  "array",
  "references",
  "guidance",
  "focal",
  "discovery",
  "stance",
  "stance-role",
):
  raise ValueError(
    "Choose baseline, repaired, prompt, batch, array, references, guidance, "
    "focal, discovery, stance or stance-role"
  )
OUT = Path(__file__).with_name(f"tool-repair-{MODE}.json")
STANCE_ONLY = MODE in ("stance", "stance-role")
RESUME = "--resume" in sys.argv
if OUT.exists() and not RESUME:
  raise RuntimeError("Evidence already exists; do not overwrite a prior run")
SAVED = json.loads(Path(__file__).with_name("preview-100-deployment.json").read_text())
DEFINITIONS_PATH = ROOT / "tests/organization/acceptance/agent_definitions.json"
DEFINITIONS = (
  json.loads(DEFINITIONS_PATH.read_text())
  if MODE
  in (
    "prompt",
    "batch",
    "array",
    "references",
    "guidance",
    "focal",
    "discovery",
    "stance",
    "stance-role",
  )
  else None
)
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
  for attempt in range(3):
    try:
      r = client.request(
        method,
        (CORE if core else PG) + path,
        json=data,
        headers={"Authorization": "Bearer " + token, "Prefer": "return=representation"},
      )
      if method == "GET" and r.status_code in (502, 503, 504) and attempt < 2:
        time.sleep(2)
        continue
      break
    except httpx.TransportError:
      if method != "GET" or attempt == 2:
        raise
      time.sleep(2)
  if r.is_error:
    raise RuntimeError(
      f"{method} {path.split('?')[0]} HTTP {r.status_code}: {r.text[:300]}"
    )
  return r.json() if r.content else None


def ids(table):
  return {row["id"] for row in call("GET", f"/{table}?select=id&limit=10000")}


def insert(table, data):
  return call("POST", "/" + table, data)[0]["id"]


TABLES = ("blocks", "relations", "jobs", "agents", "ai_models", "ai_providers")
if RESUME:
  evidence = json.loads(OUT.read_text())
  if any(table in evidence["cleanup"] for table in TABLES):
    raise RuntimeError("Cleanup already started; finish cleanup without rerunning Jobs")
  baseline = {table: set(values) for table, values in evidence["initial_ids"].items()}
  backups = evidence["config_backups"]
  configured = evidence["configured"]
  aliases = evidence["aliases"]
  evidence.setdefault("interruptions", []).append(evidence.pop("failure", "resume"))
else:
  evidence = {
    "head": subprocess.check_output(
      ["gh", "pr", "view", "100", "--json", "headRefOid", "--jq", ".headRefOid"], text=True
    ).strip(),
    "mode": MODE,
    "definition_head": subprocess.check_output(
      ["git", "rev-parse", "HEAD"], text=True
    ).strip(),
    "model": "qwen3.6-plus",
    "rounds": [],
    "cleanup": {},
  }
  baseline = {table: ids(table) for table in TABLES}
  if any(baseline.values()):
    raise RuntimeError("This acceptance run requires an empty, isolated preview")
  configs = call("GET", "/configs")
  backups = {r["key"]: r for r in configs if r["key"] in {b.config_key for b in _BEHAVIORS}}
  configured = []
  aliases = {}
  evidence.update(
    initial_ids={t: sorted(v) for t, v in baseline.items()},
    config_backups=backups,
    configured=configured,
  )


def save():
  OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2))


def snapshot():
  return {
    table: call("GET", f"/{table}?order=id&limit=10000")
    for table in ("blocks", "relations")
  }


def ensure_job(type_, parameters):
  existing = [
    row
    for row in call("GET", f"/jobs?type=eq.{type_}")
    if row["id"] not in baseline["jobs"]
  ]
  if len(existing) > 1:
    raise RuntimeError("Ambiguous Job occurrence")
  if existing:
    return existing[0]["id"]
  return insert("jobs", dict(type=type_, parameters=parameters, timeout_seconds=900))


def wait_job(ident):
  started = time.monotonic()
  last_wake = 0.0
  while time.monotonic() - started < 1000:
    # Eco web dynos can sleep despite background work; keep Core awake only
    # during acceptance. This is traffic, not a readiness gate for observations.
    if time.monotonic() - last_wake >= 60:
      try:
        client.get(CORE + "/livez", timeout=5)
      except httpx.TransportError:
        pass
      last_wake = time.monotonic()
    row = call("GET", f"/jobs?id=eq.{ident}")[0]
    if row["status"] not in ("pending", "running"):
      print("JOB", ident, row["type"], row["status"], flush=True)
      return row
    time.sleep(5)
  raise TimeoutError(f"Job {ident} remains active")


try:
  if not RESUME:
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
      if STANCE_ONLY and b.name != "evidence stance":
        continue
      saved = next(a for a in SAVED["agents"] if a["name"] == "PR100 acceptance " + b.name)
      tools = (
        saved["tools"]
        if MODE == "baseline"
        else sorted(
          set(_READ_TOOLS + b.mutation_tools + ("record_organization_candidate",))
        )
      )
      system_prompt = saved["system_prompt"]
      if DEFINITIONS is not None:
        definition = DEFINITIONS["agents"][b.name]
        tools = definition["tools"]
        system_prompt = (
          definition["system_prompt"]
          if b.name == "rumination"
          else DEFINITIONS["common_system_prompt"] + "\n\n" + definition["system_prompt"]
        )
      agent = insert(
        "agents",
        dict(
          name="PR100 tool repair " + b.name,
          model=model,
          tools=tools,
          tool_choice="auto",
          max_model_calls_per_turn=12,
          system_prompt=system_prompt,
        ),
      )
      configured.append(b.config_key)
      call(
        "PUT",
        "/configs/" + b.config_key,
        {"schema": b.config_schema, "value": {"agent": agent}},
        core=True,
      )
    if STANCE_ONLY:
      previous = json.loads(OUT.with_name("tool-repair-discovery.json").read_text())
      previous_stage = previous["rounds"][0]
      previous_job = next(
        j
        for j in previous_stage["jobs"]
        if j["job"]["type"] == "core.organization.evidence-stance.automatic.v1"
      )
      cutoff = datetime.fromisoformat(previous_job["job"]["started_at"])
      # Restore the graph before stance and the other concurrent behaviors wrote.
      for block in previous_stage["graph"]["blocks"]:
        if datetime.fromisoformat(block["created_at"]) < cutoff:
          aliases[str(block["id"])] = insert(
            "blocks", {k: block[k] for k in ("resolver", "storage", "content")}
          )
      for relation in previous_stage["graph"]["relations"]:
        if datetime.fromisoformat(relation["updated_at"]) < cutoff:
          insert(
            "relations",
            {
              "from_": aliases[str(relation["from_"])],
              "to_": aliases[str(relation["to_"])],
              "content": relation["content"],
            },
          )
      evidence["replay"] = {
        "source": "tool-repair-discovery.json",
        "source_head": previous["head"],
        "cutoff": cutoff.isoformat(),
        "seed_block_ids": [
          aliases[str(json.loads(e["input"]["content"][0]["text"])["seed_block"]["id"])]
          for e in previous_job["events"]
          if e["event"] == "agent.turn.started"
        ],
      }
    else:
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
  evidence["schedule"] = (
    "Only evidence stance: one max_seeds=3 Job with the first prior seed marked "
    "as a candidate; the remaining seeds follow ordinary automatic selection."
    if STANCE_ONLY
    else "First three behaviors sequential; remaining four independently queued. "
    "Same schedule for both versions."
  )
  if not evidence["rounds"]:
    evidence["rounds"].append({"round": 1, "jobs": []})
  stage = evidence["rounds"][0]
  if "maintenance" not in stage:
    stage["maintenance"] = wait_job(
      ensure_job(
        "core.feature_retrieval.lexical.maintain.v1", {"options": {"max_records": 10000}}
      )
    )
    save()

  def record(ident):
    if any(item["job"]["id"] == ident for item in stage["jobs"]):
      return
    completed = wait_job(ident)
    logs = call("GET", f"/logs?trace_id=eq.job.{ident}&order=id.asc&limit=10000")
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
    save()

  if STANCE_ONLY:
    descriptors = call(
      "GET", "/blocks?resolver=eq.core.organization.behavior.evidence-stance.v1&select=id"
    )
    descriptor = (
      descriptors[0]["id"]
      if descriptors
      else insert(
        "blocks",
        {"resolver": "core.organization.behavior.evidence-stance.v1", "content": ""},
      )
    )
    seed = evidence["replay"]["seed_block_ids"][0]
    candidates = call(
      "GET", f"/relations?from_=eq.{seed}&to_=eq.{descriptor}&content=eq.candidate%20for"
    )
    candidate = (
      candidates[0]["id"]
      if candidates
      else insert(
        "relations", {"from_": seed, "to_": descriptor, "content": "candidate for"}
      )
    )
    record(ensure_job("core.organization.evidence-stance.automatic.v1", {"max_seeds": 3}))
    call("DELETE", f"/relations?id=eq.{candidate}")
  else:
    for behavior in _BEHAVIORS[:3]:
      record(ensure_job(behavior.job_type, {"max_seeds": 3}))
    remaining = [ensure_job(b.job_type, {"max_seeds": 3}) for b in _BEHAVIORS[3:]]
    for ident in remaining:
      record(ident)
  stage["graph"] = snapshot()
  save()
  print(
    "WORLD", len(stage["graph"]["blocks"]), len(stage["graph"]["relations"]), flush=True
  )
except Exception as error:
  evidence["failure"] = str(error)
  print("FAILURE", str(error), flush=True)
finally:
  # Only delete this run's IDs, after all its Jobs have stopped.
  active = call("GET", "/jobs?status=in.(pending,running)&select=id")
  if active or evidence.get("failure"):
    evidence["cleanup"]["deferred_active_jobs"] = [r["id"] for r in active]
    if evidence.get("failure"):
      evidence["cleanup"]["deferred_error"] = evidence["failure"]
  else:
    evidence["cleanup"].pop("deferred_active_jobs", None)
    evidence["cleanup"].pop("deferred_error", None)
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
        call("DELETE", "/configs?key=eq." + key)
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
