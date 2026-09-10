"""Temporary, PR-100-only development logging configuration; remove after diagnosis."""

import json
import os
import time
from urllib.request import Request, urlopen


def request(url, token, *, method="GET", payload=None, heroku=False):
  headers = {
    "Authorization": f"Bearer {token}",
    "Accept": (
      "application/vnd.heroku+json; version=3" if heroku else "application/vnd.github+json"
    ),
  }
  if payload is not None:
    headers["Content-Type"] = "application/json"
  req = Request(
    url,
    data=json.dumps(payload).encode() if payload is not None else None,
    headers=headers,
    method=method,
  )
  with urlopen(req, timeout=30) as response:
    return json.load(response)


def main():
  github = "https://api.github.com/repos/InKCre/core-py"
  token = os.environ["GH_TOKEN"]
  sha = os.environ["HEAD_SHA"]
  deadline = time.monotonic() + 1800
  while time.monotonic() < deadline:
    pr = request(f"{github}/pulls/100", token)
    if (
      pr["state"] != "open"
      or pr["head"]["sha"] != sha
      or pr["head"]["ref"] != "feat/organization-nowledge-vertical"
    ):
      raise RuntimeError("PR 100 no longer selects this deployment")
    runs = request(
      f"{github}/actions/workflows/preview-deploy.yml/runs?head_sha={sha}", token
    )["workflow_runs"]
    if runs:
      latest = max(runs, key=lambda run: run["id"])
      if latest["status"] == "completed":
        if latest["conclusion"] != "success":
          raise RuntimeError("Preview deployment did not succeed")
        break
    print("Waiting for PR 100 deployment", flush=True)
    time.sleep(20)
  else:
    raise TimeoutError("Preview deployment did not finish within 30 minutes")

  expected = {
    "OBSRV__AGENT_DEBUG": "true",
    "OBSRV__LOGGING_BACKEND": "postgresql",
    "OBSRV__LOGGING_BACKEND_LEVEL": "20",
  }
  # Heroku returns all config vars. Never print or save that response.
  current = request(
    "https://api.heroku.com/apps/inkcre-core-py-pr-100/config-vars",
    os.environ["HEROKU_API_KEY"],
    method="PATCH",
    payload=expected,
    heroku=True,
  )
  if any(current.get(key) != value for key, value in expected.items()):
    raise RuntimeError("PR 100 debug configuration verification failed")
  print("PR 100 Agent debug and PostgreSQL logs enabled")


if __name__ == "__main__":
  main()
