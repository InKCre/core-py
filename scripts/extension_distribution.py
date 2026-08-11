"""Build-time verification for first-party native Extension wheels."""

from __future__ import annotations

import argparse
import configparser
from email.parser import BytesParser
import json
from pathlib import Path, PurePosixPath
import re
import tomllib
import typing
import zipfile

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version
from semantic_version import NpmSpec


ENTRY_POINT_GROUP = "inkcre.core.extensions"
_NAME_PATTERN = re.compile(
  r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?/"
  r"[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$"
)


class ProducerProject(typing.NamedTuple):
  coordinate: str
  nickname: str
  version: str
  project: str
  host_sdk: str
  host_sdk_version: str
  entry_name: str
  entry_object: str
  dependencies: tuple[str, ...]

  def prepare_document(
    self,
    *,
    source_repository: str,
    source_revision: str,
    build_id: str,
  ) -> dict[str, object]:
    return {
      "nickname": self.nickname,
      "version": self.version,
      "python": {
        "project": self.project,
        "host_sdk": self.host_sdk,
        "host_sdk_version": self.host_sdk_version,
        "entry_point": {
          "group": ENTRY_POINT_GROUP,
          "name": self.entry_name,
          "object": self.entry_object,
        },
        "source_repository": source_repository,
        "source_revision": source_revision,
        "build_id": build_id,
      },
    }


class CaseSensitiveConfigParser(configparser.ConfigParser):
  def optionxform(self, optionstr: str) -> str:
    return optionstr


def read_project(project_directory: Path) -> ProducerProject:
  pyproject = project_directory / "pyproject.toml"
  value = tomllib.loads(pyproject.read_text(encoding="utf-8"))
  project = value.get("project")
  producer = value.get("tool", {}).get("inkcre-extension")
  if not isinstance(project, dict) or not isinstance(producer, dict):
    raise ValueError(f"{pyproject} omits project or tool.inkcre-extension")
  entry_groups = project.get("entry-points")
  entries = entry_groups.get(ENTRY_POINT_GROUP) if isinstance(entry_groups, dict) else None
  if not isinstance(entries, dict) or len(entries) != 1:
    raise ValueError(f"{pyproject} must declare exactly one Core Extension entry point")
  entry_name, entry_object = next(iter(entries.items()))
  required_strings = {
    "coordinate": producer.get("name"),
    "nickname": producer.get("nickname"),
    "version": project.get("version"),
    "project": project.get("name"),
    "host_sdk": producer.get("host-sdk"),
    "host_sdk_version": producer.get("host-sdk-version"),
    "entry_name": entry_name,
    "entry_object": entry_object,
  }
  if any(not isinstance(item, str) or not item for item in required_strings.values()):
    raise ValueError(f"{pyproject} contains incomplete producer metadata")
  if _NAME_PATTERN.fullmatch(typing.cast(str, required_strings["coordinate"])) is None:
    raise ValueError(f"{pyproject} contains a noncanonical Extension Name")
  if required_strings["host_sdk"] != "core-py":
    raise ValueError(f"{pyproject} targets another Host SDK")
  try:
    NpmSpec(typing.cast(str, required_strings["host_sdk_version"]))
  except ValueError as error:
    raise ValueError(f"{pyproject} contains an invalid Host SDK SemVer range") from error
  Version(typing.cast(str, required_strings["version"]))
  dependencies = project.get("dependencies", [])
  if not isinstance(dependencies, list) or any(
    not isinstance(dependency, str) for dependency in dependencies
  ):
    raise ValueError(f"{pyproject} dependencies must be strings")
  return ProducerProject(
    **typing.cast(dict[str, str], required_strings),
    dependencies=tuple(dependencies),
  )


def verify_wheel(project: ProducerProject, wheel_path: Path) -> None:
  with zipfile.ZipFile(wheel_path) as archive:
    names = archive.namelist()
    if len(names) != len(set(names)):
      raise ValueError("wheel contains duplicate members")
    for name in names:
      path = PurePosixPath(name)
      if path.is_absolute() or "\\" in name or ".." in path.parts:
        raise ValueError("wheel contains an unsafe member")
    if "extensions/__init__.py" in names:
      raise ValueError("wheel must contribute to the PEP 420 extensions namespace")
    dist_info = {
      name.split("/", 1)[0] for name in names if name.endswith(".dist-info/METADATA")
    }
    if len(dist_info) != 1:
      raise ValueError("wheel must contain exactly one METADATA record")
    dist_info_directory = dist_info.pop()
    metadata = BytesParser().parsebytes(archive.read(f"{dist_info_directory}/METADATA"))
    entry_points = CaseSensitiveConfigParser(interpolation=None)
    entry_points.read_string(
      archive.read(f"{dist_info_directory}/entry_points.txt").decode("utf-8")
    )

  if canonicalize_name(metadata["Name"]) != canonicalize_name(project.project):
    raise ValueError("wheel Project Name differs from pyproject")
  if Version(metadata["Version"]) != Version(project.version):
    raise ValueError("wheel version differs from Extension Release")
  wheel_dependencies = {
    str(Requirement(value)) for value in metadata.get_all("Requires-Dist", [])
  }
  source_dependencies = {str(Requirement(value)) for value in project.dependencies}
  if wheel_dependencies != source_dependencies:
    raise ValueError("wheel dependencies differ from pyproject")
  if not entry_points.has_section(ENTRY_POINT_GROUP):
    raise ValueError("wheel omits the Core Extension entry-point group")
  if dict(entry_points[ENTRY_POINT_GROUP]) != {project.entry_name: project.entry_object}:
    raise ValueError("wheel entry point differs from producer metadata")


def main() -> int:
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers(dest="command", required=True)
  metadata_parser = subparsers.add_parser("metadata")
  metadata_parser.add_argument("--project", type=Path, required=True)
  metadata_parser.add_argument("--source-repository", required=True)
  metadata_parser.add_argument("--source-revision", required=True)
  metadata_parser.add_argument("--build-id", required=True)
  verify_parser = subparsers.add_parser("verify-wheel")
  verify_parser.add_argument("--project", type=Path, required=True)
  verify_parser.add_argument("--wheel", type=Path, required=True)
  args = parser.parse_args()

  project = read_project(args.project)
  if args.command == "metadata":
    print(
      json.dumps(
        {
          "coordinate": project.coordinate,
          "version": project.version,
          "project": project.project,
          "prepare": project.prepare_document(
            source_repository=args.source_repository,
            source_revision=args.source_revision,
            build_id=args.build_id,
          ),
        },
        separators=(",", ":"),
        sort_keys=True,
      )
    )
  else:
    verify_wheel(project, args.wheel)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
