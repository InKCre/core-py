"""Run the public summary command without deployment credentials or side effects."""

import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

root = Path(__file__).resolve().parents[2]
cases = (
  ("success", "false", "skipped", "skipped", "success", "未部署：", "生产发布完成："),
  ("success", "true", "success", "success", "success", "生产发布完成：", "未部署："),
  (
    "success",
    "true",
    "failure",
    "skipped",
    "failure",
    "生产发布未完成；",
    "生产发布完成：",
  ),
  (
    "success",
    "true",
    "success",
    "failure",
    "failure",
    "生产发布未完成；",
    "生产发布完成：",
  ),
  ("success", "true", "cancelled", "skipped", "cancelled", "生产发布未完成；", "未部署："),
  ("failure", "", "skipped", "skipped", "failure", "生产发布未完成；", "未部署："),
)
with TemporaryDirectory() as directory:
  summary = Path(directory) / "summary.md"
  for selection, selected, delivery, stable, job, expected, forbidden in cases:
    summary.write_text("")
    env = dict(
      os.environ,
      HEAD_SHA="verified-source",
      EVENT_NAME="workflow_run",
      JOB_STATUS=job,
      SELECTION_RESULT=selection,
      SELECTED=selected,
      DELIVERY_RESULT=delivery,
      STABLE_RESULT=stable,
      IMAGE_DIGEST="",
      GITHUB_STEP_SUMMARY=str(summary),
    )
    subprocess.run(
      ["bash", "scripts/automation/runtime_artifact.sh", "summarize-production"],
      cwd=root,
      env=env,
      check=True,
    )
    text = summary.read_text()
    assert expected in text and forbidden not in text, text
    assert "verified-source" in text and "源码声明的 Core 版本" in text, text
print("PASS: no-op, completed, delivery/stable failure, cancellation and selection failure")
