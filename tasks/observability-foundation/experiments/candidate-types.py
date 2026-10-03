"""Generate candidate client types from the task's migrated database using Supabase."""

import hashlib
import json
from pathlib import Path
import shlex
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CLIENT = ROOT.parent / "client-web"
credentials = json.loads((HERE / "runtime/database-credential.json").read_text())
url = (
  f"postgresql://postgres:{credentials['admin']}@127.0.0.1:35432/o11y_impl?sslmode=disable"
)
command = shlex.join(
  [
    "npx",
    "--yes",
    "supabase@2.112.0",
    "gen",
    "types",
    "typescript",
    "--db-url",
    url,
    "--schema",
    "inkcre",
  ]
)
script = (
  "set -eu\nworkbin=$(mktemp -d)\n"
  "trap 'rm -rf \"$workbin\"' EXIT\n"
  "ln -s '/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe' "
  '"$workbin/docker"\n'
  'PATH="$workbin:$PATH" ' + command + "\n"
)
result = subprocess.run(
  ["ssh", "-T", "-o", "BatchMode=yes", "wsl.win-ws.localhost", "bash", "-s"],
  input=script,
  capture_output=True,
  text=True,
  check=False,
  timeout=300,
)
if result.returncode:
  error = result.stderr
  for secret in credentials.values():
    error = error.replace(secret, "<lab-secret>")
  raise RuntimeError(error)
assert (
  "submission_traceparent" in result.stdout and "submission_tracestate" in result.stdout
)
formatted = subprocess.run(  # noqa: S603
  [str(CLIENT / "node_modules/.bin/oxfmt"), "--stdin-filepath", "database.generated.ts"],
  input=result.stdout,
  cwd=CLIENT,
  capture_output=True,
  text=True,
  check=True,
)
output = CLIENT / "packages/core/src/database/database.generated.ts"
output.write_text(formatted.stdout)
report = {
  "source": "candidate migrated disposable o11y_impl, not production-admitted artifact",
  "migration_head": "3d9593b0c855",
  "generator": "supabase@2.112.0",
  "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
  "required_before_merge": (
    "regenerate/compare via sync-database-contract.mjs from admitted core artifact"
  ),
}
(HERE / "runtime/candidate-types.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
