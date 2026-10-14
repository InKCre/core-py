"""Exercise the maintenance backup command with a disposable Neon API stub."""

import json
import os
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts/automation/production_maintenance.sh"


def test_snapshot_requires_completed_operation_and_exact_branch(
  tmp_path: Path,
) -> None:
  bin_directory = tmp_path / "bin"
  bin_directory.mkdir()
  calls_path = tmp_path / "calls.jsonl"
  curl = bin_directory / "curl"
  curl.write_text(
    "#!/usr/bin/env python3\n"
    "import json, os, sys\n"
    "from pathlib import Path\n"
    "args = sys.argv[1:]\n"
    "method = args[args.index('--request') + 1] if '--request' in args else 'GET'\n"
    "url = args[-1]\n"
    "with Path(os.environ['NEON_CALLS']).open('a') as calls:\n"
    "  calls.write(json.dumps({'method': method, 'url': url}) + '\\n')\n"
    "if url.endswith('/snapshots'):\n"
    "  body = {'snapshots': []}\n"
    "elif '/snapshot?' in url:\n"
    "  body = {'snapshot': {'id': 'snapshot-1', 'name': 'core-py-maintenance-41', "
    "'source_branch_id': 'br-production'}, 'operations': [{'id': 'op-1'}]}\n"
    "elif url.endswith('/operations/op-1'):\n"
    "  body = {'operation': {'status': 'finished'}}\n"
    "elif url.endswith('/snapshots/snapshot-1'):\n"
    "  body = {'snapshot': {'id': 'snapshot-1', 'name': 'core-py-maintenance-41', "
    "'source_branch_id': 'br-production'}}\n"
    "else:\n"
    "  raise SystemExit('unexpected Neon API request')\n"
    "print(json.dumps(body))\n",
    encoding="utf-8",
  )
  curl.chmod(0o755)
  date = bin_directory / "date"
  date.write_text("#!/bin/sh\nprintf '2026-11-13T00:00:00Z\n'\n", encoding="utf-8")
  date.chmod(0o755)
  output_path = tmp_path / "github-output.txt"
  summary_path = tmp_path / "summary.md"
  result = subprocess.run(  # noqa: S603 - execute the checked-in script with a local API stub.
    ["bash", str(SCRIPT), "snapshot"],
    check=False,
    capture_output=True,
    text=True,
    env={
      **os.environ,
      "PATH": f"{bin_directory}:{os.environ['PATH']}",
      "NEON_API_KEY": "test-only",
      "NEON_BRANCH_ID": "br-production",
      "NEON_PROJECT_ID": "project-1",
      "GITHUB_RUN_ID": "41",
      "GITHUB_OUTPUT": str(output_path),
      "GITHUB_STEP_SUMMARY": str(summary_path),
      "NEON_CALLS": str(calls_path),
    },
  )

  assert result.returncode == 0, result.stderr
  requests = [
    json.loads(line) for line in calls_path.read_text(encoding="utf-8").splitlines()
  ]
  assert sum(request["method"] == "POST" for request in requests) == 1
  assert any(request["url"].endswith("/operations/op-1") for request in requests)
  assert any(request["url"].endswith("/snapshots/snapshot-1") for request in requests)
  assert "snapshot_id=snapshot-1" in output_path.read_text(encoding="utf-8")
  assert "snapshot-1" in summary_path.read_text(encoding="utf-8")
