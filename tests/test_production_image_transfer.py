"""Keep exact Heroku image transfers ahead of a maintenance migration."""

import json
import os
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts/automation/production_delivery.sh"


def test_transfer_images_pushes_only_the_exact_process_tags(tmp_path: Path) -> None:
  bin_directory = tmp_path / "bin"
  bin_directory.mkdir()
  calls_path = tmp_path / "docker-calls.jsonl"
  docker = bin_directory / "docker"
  docker.write_text(
    "#!/usr/bin/env python3\n"
    "import json, os, sys\n"
    "from pathlib import Path\n"
    "args = sys.argv[1:]\n"
    "if args and args[0] == 'login':\n"
    "  sys.stdin.read()\n"
    "else:\n"
    "  with Path(os.environ['DOCKER_CALLS']).open('a') as calls:\n"
    "    calls.write(json.dumps(args) + '\\n')\n",
    encoding="utf-8",
  )
  docker.chmod(0o755)
  test_credential = "test-heroku-token-must-not-appear"
  result = subprocess.run(  # noqa: S603 - execute the checked-in script with a local CLI stub.
    ["bash", str(SCRIPT), "transfer-images"],
    check=False,
    capture_output=True,
    text=True,
    env={
      **os.environ,
      "PATH": f"{bin_directory}:{os.environ['PATH']}",
      "APP_NAME": "inkcre-owner-core",
      "HEROKU_API_KEY": test_credential,
      "HEAD_SHA": "a" * 40,
      "POSTGREST_APP_NAME": "inkcre-owner-postgrest",
      "DOCKER_CALLS": str(calls_path),
    },
  )

  assert result.returncode == 0, result.stderr
  assert test_credential not in result.stdout + result.stderr
  calls = [json.loads(line) for line in calls_path.read_text(encoding="utf-8").splitlines()]
  assert calls == [
    [
      "tag",
      f"inkcre-production-web:{'a' * 40}",
      "registry.heroku.com/inkcre-owner-core/web",
    ],
    [
      "tag",
      f"inkcre-production-release:{'a' * 40}",
      "registry.heroku.com/inkcre-owner-core/release",
    ],
    [
      "tag",
      f"inkcre-production-postgrest:{'a' * 40}",
      "registry.heroku.com/inkcre-owner-postgrest/web",
    ],
    ["push", "registry.heroku.com/inkcre-owner-core/web"],
    ["push", "registry.heroku.com/inkcre-owner-core/release"],
    ["push", "registry.heroku.com/inkcre-owner-postgrest/web"],
  ]
