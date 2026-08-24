"""Build every first-party Extension wheel and write a Toolkit preview inventory."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from inkcre_extension_toolkit.python_distribution import finalize_wheel

from extension_release import PROJECT_ROOT, discover_projects


class PreviewBuildError(RuntimeError):
  """The checked source cannot produce one unambiguous preview input set."""


def _build_wheel(project_directory: Path, output_directory: Path) -> Path:
  output_directory.mkdir(parents=True)
  environment = os.environ.copy()
  environment.setdefault("SOURCE_DATE_EPOCH", "315532800")
  result = subprocess.run(  # noqa: S603 -- arguments are structured and never use a shell
    [
      sys.executable,
      "-m",
      "build",
      "--wheel",
      "--no-isolation",
      "--outdir",
      str(output_directory),
      str(project_directory),
    ],
    cwd=PROJECT_ROOT,
    env=environment,
    check=False,
    capture_output=True,
    text=True,
  )
  if result.returncode != 0:
    detail = (result.stderr or result.stdout).strip()
    raise PreviewBuildError(
      f"could not build {project_directory.name}: {detail or f'exit {result.returncode}'}"
    )
  wheels = tuple(sorted(output_directory.glob("*.whl")))
  if len(wheels) != 1:
    raise PreviewBuildError(
      f"{project_directory.name} produced {len(wheels)} wheels instead of exactly one"
    )
  return wheels[0]


def build_preview_inputs(output_directory: Path) -> Path:
  """Build the discovered producer set into a fresh explicit Python inventory."""

  output_directory = output_directory.resolve()
  if output_directory.exists():
    raise PreviewBuildError(f"output already exists: {output_directory}")
  output_directory.mkdir(parents=True)
  distributions: list[dict[str, str]] = []
  for project in discover_projects():
    raw_wheel = _build_wheel(project.directory, output_directory / "raw" / project.key)
    wheel = finalize_wheel(
      project.directory / "pyproject.toml",
      raw_wheel,
      output_directory / "wheels" / project.key,
    )
    distributions.append(
      {
        "kind": "python",
        "producer": str(project.directory / "pyproject.toml"),
        "artifact": str(wheel),
      }
    )
  inventory = output_directory / "extensions.json"
  inventory.write_text(
    json.dumps(
      {"schema_version": 1, "distributions": distributions},
      indent=2,
      sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
  )
  return inventory


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--output", type=Path, required=True)
  args = parser.parse_args()
  print(build_preview_inputs(args.output))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
