"""Native pip acquisition into Core's interpreter and entry-point discovery."""

from __future__ import annotations

from collections.abc import Callable
from email.parser import Parser
import importlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import sysconfig
import tempfile
import typing
import zipfile

from packaging.utils import canonicalize_name, canonicalize_version
from packaging.version import InvalidVersion, Version

from .errors import (
  ExtensionAcquisitionError,
  ExtensionEntryPointError,
  ExtensionRestartRequiredError,
)
from .release import (
  ExtensionReleaseDescriptor,
  PythonReleaseDescriptor,
  simple_project_and_index_urls,
)


CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


class DistributionConsumer(typing.Protocol):
  def acquire(
    self,
    release: ExtensionReleaseDescriptor,
    association: PythonReleaseDescriptor,
  ) -> AcquiredDistribution: ...


def _run_pip(arguments: list[str]) -> subprocess.CompletedProcess[str]:
  environment = os.environ.copy()
  environment.update(
    {
      "PIP_CONFIG_FILE": os.devnull,
      "PIP_DISABLE_PIP_VERSION_CHECK": "1",
      "PIP_NO_INPUT": "1",
      "PYTHONNOUSERSITE": "1",
    }
  )
  return subprocess.run(  # noqa: S603 -- fixed interpreter and Host-owned arguments
    [sys.executable, "-m", "pip", *arguments],
    check=False,
    capture_output=True,
    env=environment,
    text=True,
  )


def _require_success(result: subprocess.CompletedProcess[str], operation: str) -> None:
  if result.returncode == 0:
    return
  detail = (result.stderr or result.stdout).strip().splitlines()
  suffix = f": {detail[-1]}" if detail else ""
  raise ExtensionAcquisitionError(f"pip {operation} failed{suffix}")


def _extension_package_name(entry_point_name: str, entry_point_object: str) -> str:
  module_name = entry_point_object.partition(":")[0]
  module_parts = module_name.split(".")
  if (
    len(module_parts) < 2
    or module_parts[0] != "extensions"
    or module_parts[1] != entry_point_name
  ):
    raise ExtensionEntryPointError(
      "Core Extension entry point must live in its declared extensions.<name> package"
    )
  return ".".join(module_parts[:2])


def _canonical_archive_path(name: str) -> PurePosixPath:
  if not name or "\\" in name:
    raise ExtensionAcquisitionError("Extension wheel contains a non-canonical path")
  path = PurePosixPath(name)
  if (
    path.is_absolute()
    or any(part in {"", ".", ".."} for part in path.parts)
    or path.as_posix() != name.rstrip("/")
  ):
    raise ExtensionAcquisitionError("Extension wheel contains a non-canonical path")
  return path


def _installed_file_owners(excluded_project: str) -> dict[Path, str]:
  owners: dict[Path, str] = {}
  for distribution in importlib.metadata.distributions():
    distribution_name = distribution.metadata["Name"] or ""
    if canonicalize_name(distribution_name) == excluded_project:
      continue
    for file in distribution.files or ():
      owners[Path(str(distribution.locate_file(file))).resolve()] = distribution_name
  return owners


def _validate_extension_wheel(
  wheel: Path,
  release: ExtensionReleaseDescriptor,
  association: PythonReleaseDescriptor,
) -> None:
  """Reject a wheel that can write outside its one namespace contribution."""
  package_name = _extension_package_name(
    association.entry_point.name,
    association.entry_point.object,
  )
  package_parts = tuple(package_name.split("."))
  project = canonicalize_name(association.project)
  try:
    with zipfile.ZipFile(wheel) as archive:
      entries = archive.infolist()
      paths = [_canonical_archive_path(entry.filename) for entry in entries]
      if any(stat.S_ISLNK(entry.external_attr >> 16) for entry in entries):
        raise ExtensionAcquisitionError("Extension wheel contains a symbolic link")
      folded = [path.as_posix().casefold() for path in paths]
      if len(folded) != len(set(folded)):
        raise ExtensionAcquisitionError("Extension wheel contains colliding archive paths")
      metadata_paths = [
        path
        for path, entry in zip(paths, entries, strict=True)
        if not entry.is_dir()
        and len(path.parts) == 2
        and path.parts[0].endswith(".dist-info")
        and path.parts[1] == "METADATA"
      ]
      if len(metadata_paths) != 1:
        raise ExtensionAcquisitionError(
          "Extension wheel does not contain exactly one Core Metadata record"
        )
      dist_info = metadata_paths[0].parts[0]
      expected_dist_info = (
        f"{project.replace('-', '_')}-"
        f"{canonicalize_version(release.version, strip_trailing_zero=False)}.dist-info"
      )
      dist_info_directories = {
        path.parts[0] for path in paths if path.parts[0].endswith(".dist-info")
      }
      if dist_info != expected_dist_info or dist_info_directories != {dist_info}:
        raise ExtensionAcquisitionError(
          "Extension wheel dist-info identity differs from its Project and Release"
        )
      metadata = Parser().parsestr(
        archive.read(metadata_paths[0].as_posix()).decode("utf-8")
      )
      wheel_paths = [
        path
        for path, entry in zip(paths, entries, strict=True)
        if not entry.is_dir()
        and len(path.parts) == 2
        and path.parts[0] == dist_info
        and path.parts[1] == "WHEEL"
      ]
      if len(wheel_paths) != 1:
        raise ExtensionAcquisitionError(
          "Extension wheel does not contain exactly one wheel metadata record"
        )
      wheel_metadata = Parser().parsestr(
        archive.read(wheel_paths[0].as_posix()).decode("utf-8")
      )
      if wheel_metadata.get("Root-Is-Purelib", "").lower() != "true":
        raise ExtensionAcquisitionError(
          "Extension wheel must install entirely into Core purelib"
        )
      if canonicalize_name(metadata.get("Name", "")) != project:
        raise ExtensionAcquisitionError(
          "Extension wheel Project differs from the Registry association"
        )
      try:
        version_matches = Version(metadata.get("Version", "")) == Version(release.version)
      except InvalidVersion as error:
        raise ExtensionAcquisitionError(
          "Extension wheel contains an invalid Project version"
        ) from error
      if not version_matches:
        raise ExtensionAcquisitionError(
          "Extension wheel version differs from the Registry Release"
        )

      files: list[PurePosixPath] = []
      for path, entry in zip(paths, entries, strict=True):
        if entry.is_dir():
          continue
        if path.suffix.casefold() == ".pth" or path.parts[0].casefold().endswith(".data"):
          raise ExtensionAcquisitionError(
            "Extension wheel contains an executable or redirected install path"
          )
        in_package = path.parts[:2] == package_parts and len(path.parts) >= 3
        in_dist_info = path.parts[0] == dist_info and len(path.parts) >= 2
        if not in_package and not in_dist_info:
          raise ExtensionAcquisitionError(
            "Extension wheel writes outside its declared package and dist-info"
          )
        files.append(path)
  except (OSError, UnicodeError, zipfile.BadZipFile) as error:
    raise ExtensionAcquisitionError("Extension wheel archive is invalid") from error

  purelib = Path(sysconfig.get_path("purelib")).resolve()
  installed_owners = _installed_file_owners(project)
  for relative in files:
    target = (purelib / relative.as_posix()).resolve()
    if not target.is_relative_to(purelib):
      raise ExtensionAcquisitionError("Extension wheel escapes Core site-packages")
    owner = installed_owners.get(target)
    if owner is not None:
      raise ExtensionAcquisitionError(
        f"Extension wheel would overwrite a file owned by Distribution {owner}"
      )


class AcquiredDistribution:
  """One exact Project installed in the Core interpreter's site-packages."""

  def __init__(
    self,
    distribution: importlib.metadata.Distribution,
    release: ExtensionReleaseDescriptor,
    association: PythonReleaseDescriptor,
  ) -> None:
    self.distribution = distribution
    self.release = release
    self.association = association
    self.entry_point = self._find_entry_point()
    files = distribution.files
    if files is None:
      raise ExtensionEntryPointError("Installed Project does not expose a file record")
    self.owned_files = {
      Path(str(distribution.locate_file(file))).resolve()
      for file in files
      if not str(file).endswith("/")
    }

  @classmethod
  def discover(
    cls,
    release: ExtensionReleaseDescriptor,
    association: PythonReleaseDescriptor,
  ) -> AcquiredDistribution:
    expected = canonicalize_name(association.project)
    matches = [
      distribution
      for distribution in importlib.metadata.distributions()
      if canonicalize_name(distribution.metadata["Name"] or "") == expected
    ]
    if len(matches) != 1:
      raise ExtensionEntryPointError(
        "Core interpreter does not contain exactly one declared Python Project"
      )
    distribution = matches[0]
    try:
      congruent = Version(distribution.version) == Version(release.version)
    except InvalidVersion as error:
      raise ExtensionEntryPointError("Installed Project version is invalid") from error
    if not congruent:
      raise ExtensionEntryPointError(
        "Installed Project version differs from the Extension Release"
      )
    return cls(distribution, release, association)

  def _find_entry_point(self) -> importlib.metadata.EntryPoint:
    declared = self.association.entry_point
    matches = [
      entry_point
      for entry_point in self.distribution.entry_points
      if entry_point.group == declared.group and entry_point.name == declared.name
    ]
    if len(matches) != 1 or matches[0].value != declared.object:
      raise ExtensionEntryPointError(
        "Installed Project entry point differs from the Registry association"
      )
    return matches[0]


class DistributionModules:
  """Load and later release one installed Extension package subtree."""

  def __init__(self, acquired: AcquiredDistribution) -> None:
    self.acquired = acquired
    self.package_name = _extension_package_name(
      acquired.entry_point.name,
      acquired.entry_point.value,
    )
    self._previous_modules: dict[str, typing.Any] = {}
    self._active = False

  def _module_names(self) -> tuple[str, ...]:
    prefix = f"{self.package_name}."
    return tuple(
      name for name in sys.modules if name == self.package_name or name.startswith(prefix)
    )

  def _is_distribution_file(self, module: typing.Any) -> bool:
    origins = (
      getattr(module, "__file__", None),
      getattr(getattr(module, "__spec__", None), "origin", None),
    )
    concrete = [Path(origin).resolve() for origin in origins if isinstance(origin, str)]
    return bool(concrete) and all(
      origin in self.acquired.owned_files for origin in concrete
    )

  def assert_origins(self) -> None:
    names = self._module_names()
    if self.package_name not in names:
      raise ExtensionEntryPointError("Extension entry-point package was not loaded")
    invalid = [name for name in names if not self._is_distribution_file(sys.modules[name])]
    if invalid:
      raise ExtensionEntryPointError(
        "Extension package did not originate from its installed wheel: "
        + ", ".join(sorted(invalid))
      )

  def load(self, extension_base: type[typing.Any]) -> type[typing.Any]:
    if self._active:
      raise ExtensionEntryPointError("Extension Distribution is already loaded")
    self._previous_modules = {name: sys.modules[name] for name in self._module_names()}
    for name in self._previous_modules:
      sys.modules.pop(name, None)
    importlib.invalidate_caches()
    try:
      extension_class = self.acquired.entry_point.load()
      self._active = True
      self.assert_origins()
      if not isinstance(extension_class, type) or not issubclass(
        extension_class, extension_base
      ):
        raise ExtensionEntryPointError(
          "Core Extension entry point does not yield an ExtensionBase subclass"
        )
      return extension_class
    except Exception:
      self.abort()
      raise

  def abort(self) -> None:
    for name in self._module_names():
      sys.modules.pop(name, None)
    sys.modules.update(self._previous_modules)
    importlib.invalidate_caches()
    self._active = False

  def unload(self) -> None:
    if not self._active:
      return
    self.assert_origins()
    self.abort()


class PipDistributionConsumer:
  """Select a Registry wheel, preflight pip, then install into Core itself."""

  def __init__(
    self,
    registry_origin: str,
    dependency_index_url: str,
    runner: CommandRunner = _run_pip,
  ) -> None:
    self.registry_origin = registry_origin
    self.dependency_index_url = dependency_index_url
    self._runner = runner
    self._restart_required_reason: str | None = None

  @staticmethod
  def _installed_versions() -> dict[str, str]:
    return {
      canonicalize_name(distribution.metadata["Name"] or ""): distribution.version
      for distribution in importlib.metadata.distributions()
      if distribution.metadata["Name"]
    }

  @staticmethod
  def _report_requirements(report: dict[str, typing.Any]) -> list[dict[str, typing.Any]]:
    installs = report.get("install")
    if not isinstance(installs, list):
      raise ExtensionAcquisitionError("pip produced an invalid install plan")
    if any(not isinstance(item, dict) for item in installs):
      raise ExtensionAcquisitionError("pip install plan has an invalid shape")
    return installs

  def _reject_replacements(
    self,
    installs: list[dict[str, typing.Any]],
    extension_project: str,
  ) -> None:
    installed_versions = self._installed_versions()
    for item in installs:
      metadata = item.get("metadata")
      if not isinstance(metadata, dict):
        raise ExtensionAcquisitionError("pip install plan omits Core Metadata")
      name = metadata.get("name")
      version = metadata.get("version")
      if not isinstance(name, str) or not isinstance(version, str):
        raise ExtensionAcquisitionError("pip install plan has invalid Core Metadata")
      installed = installed_versions.get(canonicalize_name(name))
      if (
        installed is not None
        and Version(installed) != Version(version)
        and canonicalize_name(name) != extension_project
      ):
        raise ExtensionAcquisitionError(
          f"pip plan would replace loaded Distribution {name} {installed} with {version}"
        )

  def acquire(
    self,
    release: ExtensionReleaseDescriptor,
    association: PythonReleaseDescriptor,
  ) -> AcquiredDistribution:
    project = canonicalize_name(association.project)
    if self._restart_required_reason is not None:
      raise ExtensionRestartRequiredError(self._restart_required_reason)
    _extension_package_name(
      association.entry_point.name,
      association.entry_point.object,
    )
    installed_before = self._installed_versions().get(project)
    try:
      current = AcquiredDistribution.discover(release, association)
    except ExtensionEntryPointError:
      current = None
    if current is not None:
      return current

    version = str(Version(release.version))
    _, simple_index_url = simple_project_and_index_urls(
      self.registry_origin,
      association,
    )
    with tempfile.TemporaryDirectory(prefix="inkcre-extension-") as temp_directory:
      temporary = Path(temp_directory)
      acquisition = temporary / "acquisition"
      acquisition.mkdir()
      closure = temporary / "closure"
      closure.mkdir()
      report_path = temporary / "pip-report.json"

      download = self._runner(
        [
          "download",
          "--only-binary=:all:",
          "--no-deps",
          "--dest",
          str(acquisition),
          "--index-url",
          simple_index_url,
          f"{association.project}=={version}",
        ]
      )
      _require_success(download, "wheel acquisition")
      wheels = sorted(acquisition.glob("*.whl"))
      if len(wheels) != 1:
        raise ExtensionAcquisitionError(
          "Registry Simple index did not yield exactly one compatible wheel"
        )
      _validate_extension_wheel(wheels[0], release, association)
      extension_wheel = closure / wheels[0].name
      shutil.copy2(wheels[0], extension_wheel)

      dependency_download = self._runner(
        [
          "download",
          "--only-binary=:all:",
          "--dest",
          str(closure),
          "--index-url",
          self.dependency_index_url,
          str(extension_wheel),
        ]
      )
      _require_success(dependency_download, "dependency closure acquisition")
      if not extension_wheel.is_file():
        raise ExtensionAcquisitionError(
          "pip dependency closure omitted the exact Extension wheel"
        )

      plan = self._runner(
        [
          "install",
          "--dry-run",
          "--only-binary=:all:",
          "--report",
          str(report_path),
          "--no-index",
          "--find-links",
          str(closure),
          str(extension_wheel),
        ]
      )
      _require_success(plan, "dependency preflight")
      try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
      except (OSError, json.JSONDecodeError) as error:
        raise ExtensionAcquisitionError("pip dependency report is invalid") from error
      if not isinstance(report, dict):
        raise ExtensionAcquisitionError("pip dependency report is not an object")
      installs = self._report_requirements(report)
      self._reject_replacements(installs, project)
      planned_projects = {
        canonicalize_name(typing.cast(dict[str, typing.Any], item["metadata"])["name"])
        for item in installs
      }
      if project not in planned_projects:
        raise ExtensionAcquisitionError(
          "pip did not plan the declared exact Extension Project"
        )

      self._restart_required_reason = (
        "Core site-packages mutation began; restart Core before loading Extensions"
      )
      install = self._runner(
        [
          "install",
          "--no-compile",
          "--only-binary=:all:",
          "--no-index",
          "--find-links",
          str(closure),
          str(extension_wheel),
        ]
      )
      _require_success(install, "installation")
    importlib.invalidate_caches()
    acquired = AcquiredDistribution.discover(release, association)
    if installed_before is not None:
      raise ExtensionRestartRequiredError(
        f"{association.project} was replaced; restart Core before loading it"
      )
    self._restart_required_reason = None
    return acquired
