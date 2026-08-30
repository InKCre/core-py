"""First-party Extension discovery and release-intent contract."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib
import typing


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS_DIRECTORY = PROJECT_ROOT / "extensions"
CHANGELOG_NAME = "CHANGELOG.md"
CHANGIE_VERSION = "v1.25.2"
_SEMVER_IDENTIFIER = r"(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
_SEMVER_PATTERN = re.compile(
  rf"^(0|[1-9][0-9]*)[.](0|[1-9][0-9]*)[.](0|[1-9][0-9]*)"
  rf"(?:-({_SEMVER_IDENTIFIER}(?:[.]{_SEMVER_IDENTIFIER})*))?$"
)


class ReleaseContractError(RuntimeError):
  """The checked repository cannot produce an unambiguous Extension Release."""


@dataclass(frozen=True)
class SemanticVersion:
  major: int
  minor: int
  patch: int
  prerelease: tuple[str, ...] = ()

  @classmethod
  def parse(cls, value: str) -> SemanticVersion:
    match = _SEMVER_PATTERN.fullmatch(value)
    if match is None:
      raise ReleaseContractError(f"{value!r} is not a canonical Release SemVer")
    prerelease = tuple(match.group(4).split(".")) if match.group(4) else ()
    return cls(
      major=int(match.group(1)),
      minor=int(match.group(2)),
      patch=int(match.group(3)),
      prerelease=prerelease,
    )

  def compare(self, other: SemanticVersion) -> int:
    stable = (self.major, self.minor, self.patch)
    other_stable = (other.major, other.minor, other.patch)
    if stable != other_stable:
      return 1 if stable > other_stable else -1
    if not self.prerelease or not other.prerelease:
      if self.prerelease == other.prerelease:
        return 0
      return 1 if not self.prerelease else -1
    for left, right in zip(self.prerelease, other.prerelease, strict=False):
      if left == right:
        continue
      left_numeric = left.isdigit()
      right_numeric = right.isdigit()
      if left_numeric and right_numeric:
        return 1 if int(left) > int(right) else -1
      if left_numeric != right_numeric:
        return -1 if left_numeric else 1
      return 1 if left > right else -1
    if len(self.prerelease) == len(other.prerelease):
      return 0
    return 1 if len(self.prerelease) > len(other.prerelease) else -1


@dataclass(frozen=True)
class ExtensionProject:
  key: str
  directory: Path
  coordinate: str
  version: SemanticVersion

  @property
  def version_text(self) -> str:
    value = f"{self.version.major}.{self.version.minor}.{self.version.patch}"
    if self.version.prerelease:
      value += f"-{'.'.join(self.version.prerelease)}"
    return value

  @property
  def changelog(self) -> Path:
    return self.directory / CHANGELOG_NAME

  @property
  def version_entry(self) -> Path:
    return PROJECT_ROOT / ".changes" / self.key / f"{self.version_text}.md"


def _read_project_value(value: dict[str, typing.Any], directory: Path) -> ExtensionProject:
  project = value.get("project")
  producer = value.get("tool", {}).get("inkcre-extension")
  if not isinstance(project, dict) or not isinstance(producer, dict):
    raise ReleaseContractError(
      f"{directory / 'pyproject.toml'} omits project or tool.inkcre-extension"
    )
  version = project.get("version")
  coordinate = producer.get("name")
  if not isinstance(version, str) or not isinstance(coordinate, str):
    raise ReleaseContractError(f"{directory / 'pyproject.toml'} omits Release identity")
  return ExtensionProject(
    key=directory.name,
    directory=directory,
    coordinate=coordinate,
    version=SemanticVersion.parse(version),
  )


def read_project(directory: Path) -> ExtensionProject:
  pyproject = directory / "pyproject.toml"
  return _read_project_value(
    tomllib.loads(pyproject.read_text(encoding="utf-8")),
    directory,
  )


def discover_projects() -> tuple[ExtensionProject, ...]:
  projects: list[ExtensionProject] = []
  for directory in sorted(EXTENSIONS_DIRECTORY.iterdir()):
    pyproject = directory / "pyproject.toml"
    if not directory.is_dir() or not pyproject.is_file():
      continue
    value = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    if not isinstance(value.get("tool", {}).get("inkcre-extension"), dict):
      continue
    projects.append(_read_project_value(value, directory))
  if not projects:
    raise ReleaseContractError("no first-party Extension projects were discovered")
  return tuple(projects)


def project_by_key(key: str) -> ExtensionProject:
  projects = {project.key: project for project in discover_projects()}
  try:
    return projects[key]
  except KeyError as error:
    raise ReleaseContractError(f"unknown first-party Extension project {key!r}") from error


def _run(
  arguments: list[str],
  *,
  check: bool = True,
) -> subprocess.CompletedProcess[str]:
  result = subprocess.run(  # noqa: S603 -- arguments are structured and never use a shell
    arguments,
    cwd=PROJECT_ROOT,
    check=False,
    capture_output=True,
    text=True,
  )
  if check and result.returncode != 0:
    detail = (result.stderr or result.stdout).strip()
    raise ReleaseContractError(
      f"{' '.join(arguments)} failed: {detail or f'exit {result.returncode}'}"
    )
  return result


def _git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
  return _run(["git", *arguments], check=check)


def _changie(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
  executable = os.environ.get("CHANGIE", "changie")
  try:
    return _run([executable, *arguments], check=check)
  except FileNotFoundError as error:
    raise ReleaseContractError(
      "Changie is required; install the pinned project version before release work"
    ) from error


def _project_at_revision(
  project: ExtensionProject, revision: str
) -> ExtensionProject | None:
  relative = project.directory.relative_to(PROJECT_ROOT) / "pyproject.toml"
  result = _git("show", f"{revision}:{relative.as_posix()}", check=False)
  if result.returncode != 0:
    return None
  return _read_project_value(tomllib.loads(result.stdout), project.directory)


def _artifact_changed(
  project: ExtensionProject,
  base: str,
  head: str | None = "HEAD",
) -> bool:
  relative = project.directory.relative_to(PROJECT_ROOT).as_posix()
  revisions = [base] if head is None else [base, head]
  result = _git(
    "diff",
    "--quiet",
    *revisions,
    "--",
    relative,
    f":(exclude){relative}/{CHANGELOG_NAME}",
    check=False,
  )
  if result.returncode not in {0, 1}:
    raise ReleaseContractError(
      f"could not compare {project.key} artifact input across {base}..{head}"
    )
  return result.returncode == 1


def _validate_changie_state(project: ExtensionProject) -> list[str]:
  problems: list[str] = []
  if not project.changelog.is_file():
    problems.append(f"{project.key}: missing {project.changelog.relative_to(PROJECT_ROOT)}")
  if not project.version_entry.is_file():
    problems.append(
      f"{project.key}: missing {project.version_entry.relative_to(PROJECT_ROOT)}"
    )
  latest = _changie("latest", "--project", project.key, check=False)
  expected = f"{project.key}-{project.version_text}"
  if latest.returncode != 0:
    detail = (latest.stderr or latest.stdout).strip()
    problems.append(f"{project.key}: Changie project unavailable: {detail}")
  elif latest.stdout.strip() != expected:
    problems.append(
      f"{project.key}: Changie latest {latest.stdout.strip()!r} != {expected!r}"
    )
  dry_run = _changie(
    "batch",
    "auto",
    "--project",
    project.key,
    "--dry-run",
    check=False,
  )
  no_changes = "no unreleased changes found for automatic bumping"
  detail = f"{dry_run.stdout}\n{dry_run.stderr}"
  if dry_run.returncode != 0 and no_changes not in detail:
    problems.append(f"{project.key}: invalid unreleased changes: {detail.strip()}")
  return problems


def _validate_changie_binary() -> list[str]:
  result = _changie("--version", check=False)
  if result.returncode == 0 and result.stdout.strip() == (
    f"changie version {CHANGIE_VERSION}"
  ):
    return []
  detail = (result.stderr or result.stdout).strip()
  return [
    f"Changie {CHANGIE_VERSION} is required; found {detail or 'an unavailable binary'}"
  ]


def _validate_merged_changelogs(
  projects: tuple[ExtensionProject, ...],
) -> list[str]:
  if any(not project.changelog.is_file() for project in projects):
    return []
  expected = "".join(project.changelog.read_text(encoding="utf-8") for project in projects)
  generated = _changie("merge", "--dry-run", check=False)
  if generated.returncode != 0:
    detail = (generated.stderr or generated.stdout).strip()
    return [f"Changie could not regenerate changelogs: {detail}"]
  if generated.stdout != expected:
    return ["generated Extension changelogs differ from their Changie version entries"]
  return []


def check_release_contract(base: str | None = None) -> None:
  projects = discover_projects()
  problems = _validate_changie_binary()
  for project in projects:
    problems.extend(_validate_changie_state(project))
  problems.extend(_validate_merged_changelogs(projects))

  if base is not None:
    if _git("merge-base", "--is-ancestor", base, "HEAD", check=False).returncode != 0:
      problems.append(f"{base} is not an ancestor of HEAD")
    else:
      for project in projects:
        previous = _project_at_revision(project, base)
        if previous is None:
          continue
        if (
          _artifact_changed(project, base, head=None)
          and project.version.compare(previous.version) <= 0
        ):
          problems.append(
            f"{project.key}: artifact input changed without advancing "
            f"{previous.version_text}"
          )

  if problems:
    raise ReleaseContractError("\n".join(f"- {problem}" for problem in problems))


def version_changed(project: ExtensionProject, base: str) -> bool:
  previous = _project_at_revision(project, base)
  return previous is None or previous.version != project.version


def verify_artifact_unchanged(
  project: ExtensionProject,
  from_revision: str,
  to_revision: str,
) -> None:
  if _artifact_changed(project, from_revision, to_revision):
    raise ReleaseContractError(
      f"{project.key} artifact input changed across {from_revision}..{to_revision}"
    )


def prepare_release(project: ExtensionProject) -> None:
  problems = _validate_changie_binary()
  if problems:
    raise ReleaseContractError("\n".join(f"- {problem}" for problem in problems))
  _changie("batch", "auto", "--project", project.key)
  _changie("merge")
  updated = project_by_key(project.key)
  problems = _validate_changie_state(updated)
  if problems:
    raise ReleaseContractError("\n".join(f"- {problem}" for problem in problems))


def render_version_pr_body() -> str:
  releases: list[str] = []
  no_changes = "no unreleased changes found for automatic bumping"
  for project in discover_projects():
    next_version = _changie("next", "auto", "--project", project.key, check=False)
    if next_version.returncode != 0:
      detail = f"{next_version.stdout}\n{next_version.stderr}".strip()
      if no_changes in detail:
        continue
      raise ReleaseContractError(
        f"could not determine the next {project.key} version: {detail}"
      )
    prefix = f"{project.key}-"
    value = next_version.stdout.strip()
    if not value.startswith(prefix):
      raise ReleaseContractError(
        f"Changie next returned unexpected {project.key} version {value!r}"
      )
    notes = (
      _changie("batch", "auto", "--project", project.key, "--dry-run")
      .stdout.partition("\n")[2]
      .strip()
    )
    releases.append(f"## {project.coordinate}@{value.removeprefix(prefix)}\n\n{notes}")

  introduction = (
    "This PR is maintained automatically from the pending first-party Extension "
    "Changie fragments. Merge it when these Releases are ready to publish; new "
    "fragments reaching main will update this PR.\n\n# Releases"
  )
  return f"{introduction}\n\n{'\n\n'.join(releases)}\n"


def main() -> int:
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers(dest="command", required=True)
  projects_parser = subparsers.add_parser("projects")
  projects_parser.add_argument("--json", action="store_true")
  check_parser = subparsers.add_parser("check")
  check_parser.add_argument("--base")
  prepare_parser = subparsers.add_parser("prepare")
  prepare_parser.add_argument("project")
  subparsers.add_parser("version-pr-body")
  changed_parser = subparsers.add_parser("version-changed")
  changed_parser.add_argument("--project", required=True)
  changed_parser.add_argument("--base", required=True)
  unchanged_parser = subparsers.add_parser("verify-artifact-unchanged")
  unchanged_parser.add_argument("--project", required=True)
  unchanged_parser.add_argument("--from", dest="from_revision", required=True)
  unchanged_parser.add_argument("--to", dest="to_revision", required=True)
  args = parser.parse_args()

  try:
    if args.command == "projects":
      keys = [project.key for project in discover_projects()]
      print(json.dumps(keys, separators=(",", ":")) if args.json else "\n".join(keys))
    elif args.command == "check":
      check_release_contract(args.base)
    elif args.command == "prepare":
      prepare_release(project_by_key(args.project))
    elif args.command == "version-pr-body":
      print(render_version_pr_body(), end="")
    elif args.command == "version-changed":
      print(str(version_changed(project_by_key(args.project), args.base)).lower())
    else:
      verify_artifact_unchanged(
        project_by_key(args.project),
        args.from_revision,
        args.to_revision,
      )
  except ReleaseContractError as error:
    print(error, file=sys.stderr)
    return 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
