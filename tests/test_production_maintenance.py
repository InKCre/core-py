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
    "output_file = args[args.index('--output') + 1] if '--output' in args else None\n"
    "headers = [args[index + 1] for index, value in enumerate(args[:-1]) "
    "if value == '--header']\n"
    "with Path(os.environ['NEON_CALLS']).open('a') as calls:\n"
    "  record = {'method': method, 'url': url, 'headers': headers}\n"
    "  calls.write(json.dumps(record) + '\\n')\n"
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
    "if output_file:\n"
    "  Path(output_file).write_text(json.dumps(body))\n"
    "  print('200')\n"
    "else:\n"
    "  print(json.dumps(body))\n",
    encoding="utf-8",
  )
  curl.chmod(0o755)
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
  post_requests = [request for request in requests if request["method"] == "POST"]
  assert len(post_requests) == 1
  assert post_requests[0]["url"].endswith(
    "/branches/br-production/snapshot?name=core-py-maintenance-41"
  )
  assert any(request["url"].endswith("/operations/op-1") for request in requests)
  assert any(request["url"].endswith("/snapshots/snapshot-1") for request in requests)
  assert "snapshot_id=snapshot-1" in output_path.read_text(encoding="utf-8")
  assert "snapshot-1" in summary_path.read_text(encoding="utf-8")


def test_snapshot_reports_neon_http_error_without_exposing_request_credentials(
  tmp_path: Path,
) -> None:
  bin_directory = tmp_path / "bin"
  bin_directory.mkdir()
  curl = bin_directory / "curl"
  curl.write_text(
    "#!/usr/bin/env python3\n"
    "import json, sys\n"
    "from pathlib import Path\n"
    "args = sys.argv[1:]\n"
    "url = args[-1]\n"
    "output_file = args[args.index('--output') + 1] if '--output' in args else None\n"
    "if url.endswith('/snapshots'):\n"
    "  print(json.dumps({'snapshots': []}))\n"
    "elif output_file:\n"
    "  Path(output_file).write_text(json.dumps({'code': 'invalid_snapshot', "
    "'message': 'snapshot request rejected'}))\n"
    "  print('422')\n"
    "else:\n"
    "  raise SystemExit('unexpected Neon API request')\n",
    encoding="utf-8",
  )
  curl.chmod(0o755)
  result = subprocess.run(  # noqa: S603 - execute the checked-in script with a local API stub.
    ["bash", str(SCRIPT), "snapshot"],
    check=False,
    capture_output=True,
    text=True,
    env={
      **os.environ,
      "PATH": f"{bin_directory}:{os.environ['PATH']}",
      "NEON_API_KEY": "test-only-secret",
      "NEON_BRANCH_ID": "br-production",
      "NEON_PROJECT_ID": "project-1",
      "GITHUB_RUN_ID": "42",
    },
  )

  assert result.returncode == 1
  assert "HTTP 422" in result.stderr
  assert "invalid_snapshot" in result.stderr
  assert "snapshot request rejected" in result.stderr
  assert "test-only-secret" not in result.stderr
