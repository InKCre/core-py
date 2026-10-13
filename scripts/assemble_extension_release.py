"""Capture and publish one fixed-source candidate for first-party Extensions."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess

from build_extension_preview import _build_wheel
from extension_distribution import read_project, verify_wheel
from scripts.release import discover_projects


ARTIFACT_NAME = "first-party-extension-candidate"
SOURCE_REPOSITORY = "https://github.com/InKCre/core-py"
WEB_REPOSITORY = "https://github.com/InKCre/client-web"


def release_toolkit(module: str):
  """Load optional publisher modules only for release commands that need them."""
  return importlib.import_module(f"inkcre_extension_toolkit.{module}")


def run(*arguments: str, env: dict[str, str] | None = None) -> str:
  return subprocess.check_output(  # noqa: S603 -- structured arguments, no shell
    arguments, text=True, env=env
  ).strip()


def sha256(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def write_plan(directory: Path, plan: dict) -> None:
  (directory / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")


def create_plan(directory: Path, web_revision: str, registry_url: str) -> None:
  if not re.fullmatch(r"[0-9a-f]{40}", web_revision):
    raise ValueError("Web source must be a full commit SHA")
  if not registry_url:
    raise ValueError("Registry URL is required")
  build_id = os.environ["GITHUB_RUN_ID"]
  core_revision = run("git", "rev-parse", "HEAD")
  candidates = []
  for project in discover_projects(extensions_only=True):
    environment = {
      **os.environ,
      "EXTENSION": project.key,
      "GITHUB_OUTPUT": "",
    }
    selected = run(
      "bash", "scripts/automation/extension_publication.sh", "select", env=environment
    )
    if selected != "selected=true":
      continue
    producer = read_project(project.directory)
    candidates.append(
      {
        "directory": project.key,
        "name": producer.coordinate,
        "version": producer.version,
        "prepare": producer.prepare_document(
          source_repository=SOURCE_REPOSITORY,
          source_revision=core_revision,
          build_id=build_id,
        ),
      }
    )
  directory.mkdir(parents=True)
  write_plan(
    directory,
    {
      "registry_url": registry_url,
      "core_revision": core_revision,
      "web_revision": web_revision,
      "build_id": build_id,
      "candidates": candidates,
    },
  )
  output_file = os.environ.get("GITHUB_OUTPUT")
  if output_file:
    with Path(output_file).open("a") as output:
      output.write(f"has_candidates={str(bool(candidates)).lower()}\n")


def build_wheels(directory: Path) -> None:
  plan = json.loads((directory / "plan.json").read_text())
  projects = {project.key: project for project in discover_projects(extensions_only=True)}
  for candidate in plan["candidates"]:
    project = projects.get(candidate["directory"])
    if project is None:
      raise ValueError("Candidate names an unknown Core Extension")
    output = directory / candidate["directory"]
    output.mkdir(exist_ok=True)
    project_directory = project.directory
    producer = read_project(project_directory)
    if producer.coordinate != candidate["name"] or producer.version != candidate["version"]:
      raise ValueError("Selected Core project identity or version changed")
    raw = _build_wheel(project_directory, output / "raw")
    wheel = release_toolkit("python_distribution").finalize_wheel(
      project_directory / "pyproject.toml", raw, output
    )
    verify_wheel(producer, wheel)
    raw.unlink()
    raw.parent.rmdir()
    candidate["python"] = {
      "file": wheel.relative_to(directory).as_posix(),
      "sha256": sha256(wheel),
    }
  write_plan(directory, plan)


def _artifact_path(directory: Path, artifact: dict) -> Path:
  file = directory / artifact["file"]
  if not file.resolve().is_relative_to(directory.resolve()):
    raise ValueError("Candidate artifact escapes its saved directory")
  if sha256(file) != artifact["sha256"]:
    raise ValueError("Saved artifact digest differs")
  return file


def check_candidate(directory: Path, registry_url: str) -> dict:
  plan = json.loads((directory / "plan.json").read_text())
  if plan["registry_url"] != registry_url:
    raise ValueError("Candidate belongs to another Registry")
  if plan["core_revision"] != run("git", "rev-parse", "HEAD"):
    raise ValueError("Candidate belongs to another Core source")
  if not re.fullmatch(r"[0-9a-f]{40}", plan["web_revision"]):
    raise ValueError("Candidate Web source is not a full commit SHA")
  if plan["build_id"] != os.environ["GITHUB_RUN_ID"]:
    raise ValueError("Candidate belongs to another workflow run")
  projects = {project.key: project for project in discover_projects(extensions_only=True)}
  directories = set()
  names = set()
  for candidate in plan["candidates"]:
    if candidate["directory"] in directories or candidate["name"] in names:
      raise ValueError("Candidate contains duplicate Extension identities")
    directories.add(candidate["directory"])
    names.add(candidate["name"])
    project = projects.get(candidate["directory"])
    if project is None:
      raise ValueError("Candidate names an unknown Core Extension")
    producer = read_project(project.directory)
    if producer.coordinate != candidate["name"] or producer.version != candidate["version"]:
      raise ValueError("Candidate differs from the fixed Core producer metadata")
    prepare = release_toolkit("contracts").PrepareReleaseRequest.model_validate(
      candidate["prepare"]
    )
    if prepare.version != candidate["version"]:
      raise ValueError("Candidate version differs from prepare")
    python = candidate.get("python")
    python_association = prepare.python
    if python is None:
      raise ValueError("Candidate omits Python bytes")
    if python_association is None:
      raise ValueError("Candidate omits Python association")
    if python_association.source_repository != SOURCE_REPOSITORY:
      raise ValueError("Candidate Python provenance differs")
    if python_association.source_revision != plan["core_revision"]:
      raise ValueError("Python provenance differs from fixed Core source")
    if python_association.build_id != plan["build_id"]:
      raise ValueError("Python build ID differs from candidate")
    _artifact_path(directory, python)
    module_federation = candidate.get("module_federation")
    if (module_federation is None) != (prepare.module_federation is None):
      raise ValueError("Candidate omits declared Module Federation bytes")
    if module_federation is not None:
      association = prepare.module_federation
      if association is None:
        raise ValueError("Candidate omits Module Federation association")
      if association.source_repository != WEB_REPOSITORY:
        raise ValueError("Candidate Module Federation provenance differs")
      if association.source_revision != plan["web_revision"]:
        raise ValueError("Module Federation provenance differs from fixed Web source")
      if association.build_id != plan["build_id"]:
        raise ValueError("Module Federation build ID differs from candidate")
      _artifact_path(directory, module_federation)
  return plan


def publish(directory: Path, registry_url: str) -> None:
  plan = check_candidate(directory, registry_url)
  token = os.environ["INKCRE_EXTENSION_REGISTRY_TOKEN"]
  prepared = []
  with release_toolkit("client").RegistryClient(registry_url, token=token) as registry:
    for candidate in plan["candidates"]:
      namespace, name = candidate["name"].split("/")
      prepare = release_toolkit("contracts").PrepareReleaseRequest.model_validate(
        candidate["prepare"]
      )
      registry.prepare(namespace, name, prepare)
      prepared.append((candidate, namespace, name, prepare))

    for candidate, namespace, name, prepare in prepared:
      subprocess.run(  # noqa: S603 -- uv owns native Python publication
        [
          "uv",
          "publish",
          "--publish-url",
          registry_url.rstrip("/") + "/legacy/",
          str(directory / candidate["python"]["file"]),
        ],
        env={**os.environ, "UV_PUBLISH_TOKEN": token},
        check=True,
      )
      if prepare.module_federation is not None:
        registry.upload_module_federation(
          namespace,
          name,
          candidate["version"],
          (directory / candidate["module_federation"]["file"]).read_bytes(),
        )

    for candidate, namespace, name, prepare in prepared:
      registry.publish(namespace, name, candidate["version"])
      visible = registry.get_release(namespace, name, candidate["version"])
      if visible.python is None or (
        prepare.module_federation is not None and visible.module_federation is None
      ):
        raise ValueError("Published Release omits a planned Distribution")
      print(f"{candidate['name']} {candidate['version']}: complete and published")


def locate() -> None:
  pages = json.loads(
    run(
      "gh",
      "api",
      f"repos/{os.environ['GITHUB_REPOSITORY']}/actions/runs/"
      f"{os.environ['GITHUB_RUN_ID']}/artifacts",
      "--paginate",
      "--slurp",
    )
  )
  artifacts = [
    item for page in pages for item in page["artifacts"] if item["name"] == ARTIFACT_NAME
  ]
  if len(artifacts) != 1 or artifacts[0]["expired"]:
    raise ValueError("Original candidate is missing, ambiguous, or expired; do not rebuild")
  with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
    output.write(f"artifact_id={artifacts[0]['id']}\n")


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("command", choices=("plan", "build", "check", "publish", "locate"))
  parser.add_argument("--directory", type=Path, default=Path(".extension-delivery"))
  parser.add_argument("--web-revision")
  args = parser.parse_args()
  if args.command == "locate":
    locate()
    return
  registry_url = os.environ["INKCRE_EXTENSION_REGISTRY_URL"]
  directory = args.directory.resolve()
  if args.command == "plan":
    if args.web_revision is None:
      raise ValueError("--web-revision is required")
    create_plan(directory, args.web_revision, registry_url)
  elif args.command == "build":
    build_wheels(directory)
  elif args.command == "check":
    check_candidate(directory, registry_url)
  else:
    publish(directory, registry_url)


if __name__ == "__main__":
  main()
