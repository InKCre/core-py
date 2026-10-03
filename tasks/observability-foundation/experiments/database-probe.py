"""Actual legacy native writes plus candidate DDL in the dedicated disposable database."""

import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
CREDENTIALS = json.loads((HERE / "runtime/database-credential.json").read_text())
ADMIN_URL = f"postgresql://postgres:{CREDENTIALS['admin']}@127.0.0.1:35432/o11y_lab"
CORE_URL = (
  f"postgresql+psycopg://inkcre_core:{CREDENTIALS['core']}@127.0.0.1:35432/o11y_lab"
)
# The dedicated database, port and credentials come only from this lab. Never use .env URLs.
os.environ.update(
  MIGRATION_DATABASE_URL=ADMIN_URL, DATABASE_URL=CORE_URL, INKCRE_ENV_FILE=""
)

import psycopg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.database_contract.readiness import check_database_contract
from app.persistence.job.repository import JobRepository
from app.schemas.job import JobModel, JobStatus
from scripts.verify_postgrest_contract import _token


async def native_writes(new_id):
  engine = create_async_engine(CORE_URL)
  try:
    async with AsyncSession(engine) as session:
      async with session.begin():
        repository = JobRepository(session)
        old = await repository.create(JobModel(type="o11y-lab", timeout_seconds=30))
        old_id = old.id
        new = await repository.get(new_id)
        assert new is not None and new.status == JobStatus.PENDING
        assert not hasattr(new, "submission_traceparent")
        claimed = await repository.claim(new_id)
        assert claimed is not None
        claimed.state = {"synthetic": "native-finished"}
        assert await repository.close(claimed, JobStatus.FINISHED)
    return old_id
  finally:
    await engine.dispose()


def main(action):
  if action == "init":
    env = {
      **os.environ,
      "CORE_DATABASE_PASSWORD": CREDENTIALS["core"],
      "POSTGREST_DATABASE_PASSWORD": CREDENTIALS["rest"],
    }
    result = subprocess.run(
      [sys.executable, "scripts/database.py", "init", "--profile", "development"],
      cwd=ROOT,
      env=env,
      check=False,
      text=True,
      capture_output=True,
    )
    (HERE / "runtime/database-init.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, (
      "Initialization failed; inspect local ignored runtime log"
    )
    print("Dedicated database initialized using existing lifecycle")
  elif action == "probe":
    baseline = check_database_contract("development", CORE_URL).as_dict()
    assert baseline["status"] == "ok", baseline
    carrier = {
      "submission_traceparent": "00-" + "1" * 32 + "-" + "2" * 16 + "-01",
      "submission_tracestate": "inkcre=synthetic",
    }
    with psycopg.connect(ADMIN_URL) as conn:
      conn.execute(
        "ALTER TABLE inkcre.jobs ADD COLUMN submission_traceparent text CHECK (octet_length(submission_traceparent) <= 512), ADD COLUMN submission_tracestate text CHECK (octet_length(submission_tracestate) <= 512)"  # noqa: E501
      )
      conn.execute(
        "INSERT INTO inkcre.job_types (id, description, parameters_schema, default_timeout_seconds) VALUES ('o11y-lab', 'synthetic compatibility probe', '{}', 30)"  # noqa: E501
      )
      row = conn.execute(
        "INSERT INTO inkcre.jobs (type, timeout_seconds, submission_traceparent, submission_tracestate) VALUES ('o11y-lab', 30, %s, %s) RETURNING id",  # noqa: E501
        tuple(carrier.values()),
      ).fetchone()
      new_id = row[0]
    old_id = asyncio.run(native_writes(new_id))
    with psycopg.connect(ADMIN_URL) as conn:
      stored = conn.execute(
        "SELECT status, state, submission_traceparent, submission_tracestate FROM inkcre.jobs WHERE id=%s",  # noqa: E501
        (new_id,),
      ).fetchone()
      assert stored[0] == "finished" and stored[1] == {"synthetic": "native-finished"}
      assert stored[2:] == tuple(carrier.values())
      assert conn.execute(
        "SELECT submission_traceparent, submission_tracestate FROM inkcre.jobs WHERE id=%s",
        (old_id,),
      ).fetchone() == (None, None)
      bounded = conn.execute(
        "INSERT INTO inkcre.jobs (type, timeout_seconds, submission_traceparent) VALUES ('o11y-lab', 30, %s) RETURNING id",  # noqa: E501
        ("broken",),
      ).fetchone()[0]
      try:
        with conn.transaction():
          conn.execute(
            "INSERT INTO inkcre.jobs (type, timeout_seconds, submission_tracestate) VALUES ('o11y-lab', 30, %s)",  # noqa: E501
            ("x" * 513,),
          )
      except psycopg.errors.CheckViolation:
        capacity_rejected = True
      else:
        raise AssertionError("Oversized carrier not rejected")
      original_heads = conn.execute(
        "SELECT version_num FROM public.alembic_version"
      ).fetchall()
      assert len(original_heads) == 1
      conn.execute("UPDATE public.alembic_version SET version_num='o11y_probe_candidate'")
    try:
      next_schema = check_database_contract("development", CORE_URL).as_dict()
      assert (
        next_schema["status"] == "error" and next_schema["migration"]["status"] == "error"
      )
    finally:
      with psycopg.connect(ADMIN_URL) as conn:
        conn.execute("UPDATE public.alembic_version SET version_num=%s", original_heads[0])
    with psycopg.connect(ADMIN_URL) as conn:
      ts_id = conn.execute(
        "INSERT INTO inkcre.jobs (type, timeout_seconds, submission_traceparent, submission_tracestate) VALUES ('o11y-lab', 30, %s, %s) RETURNING id",  # noqa: E501
        tuple(carrier.values()),
      ).fetchone()[0]
      conn.execute("NOTIFY pgrst, 'reload schema'")
    # Short-lived synthetic credential used only by the local PostgREST probe, never
    # archived.
    payload = {
      "baseUrl": "http://127.0.0.1:33000",
      "token": _token(CREDENTIALS["jwt"]),
      "jobId": ts_id,
      "carrier": carrier,
    }
    path = HERE / "runtime/database-client.json"
    with os.fdopen(os.open(path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600), "w") as f:
      json.dump(payload, f)
    report = {
      "baseline": baseline,
      "legacy_native_insert_defaults_null": True,
      "legacy_native_claim_close_preserve_carrier": True,
      "bounded_semantically_invalid_record": bounded,
      "over_512_bytes_rejected": capacity_rejected,
      "simulated_new_head_old_readiness": next_schema,
      "head_restored": True,
      "note": "Candidate DDL and synthetic head marker only; no production migration or full runtime boot",  # noqa: E501
    }
    (HERE / "runtime/database-probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
      json.dumps(
        {
          key: value
          for key, value in report.items()
          if key not in {"baseline", "simulated_new_head_old_readiness"}
        },
        indent=2,
      )
    )
  else:
    raise SystemExit("Use init or probe")


if __name__ == "__main__":
  main(sys.argv[1])
