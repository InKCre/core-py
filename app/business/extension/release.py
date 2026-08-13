"""Exact Extension Release reader and Core Host compatibility precheck."""

from __future__ import annotations

import re
import typing
from urllib.parse import urljoin, urlsplit, urlunsplit

from packaging.utils import canonicalize_name
import pydantic
import requests  # pyrefly: ignore[untyped-import]
from semantic_version import NpmSpec, Version

from app.version import CORE_VERSION

from .errors import ExtensionCompatibilityError, ExtensionRegistryError


CORE_HOST_SDK = "core-py"
CORE_HOST_SDK_VERSION = CORE_VERSION
ENTRY_POINT_GROUP = "inkcre.core.extensions"
_SEGMENT_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$")
_SEMVER_PATTERN = re.compile(
  r"^(0|[1-9][0-9]*)[.](0|[1-9][0-9]*)[.](0|[1-9][0-9]*)"
  r"(-(0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
  r"([.](0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?$"
)


class EntryPointDescriptor(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid")

  group: str
  name: str
  object: str


class PythonReleaseDescriptor(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid")

  project: str
  simple_url: str
  host_sdk: str
  host_sdk_version: str
  entry_point: EntryPointDescriptor


class ExtensionReleaseDescriptor(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid")

  name: str
  nickname: str
  version: str
  state: str
  python: PythonReleaseDescriptor | None = None
  module_federation: dict | None = None


class ReleaseResolver(typing.Protocol):
  def get(self, name: str, version: str) -> ExtensionReleaseDescriptor: ...


def validate_coordinate(name: str, version: str | None = None) -> tuple[str, str]:
  parts = name.split("/")
  if len(parts) != 2 or any(_SEGMENT_PATTERN.fullmatch(part) is None for part in parts):
    raise ExtensionCompatibilityError("Extension Name is not canonical")
  if version is not None and _SEMVER_PATTERN.fullmatch(version) is None:
    raise ExtensionCompatibilityError("Extension Release version is not strict SemVer")
  return parts[0], parts[1]


class RegistryReleaseClient:
  def __init__(self, origin: str, timeout: float) -> None:
    self.origin = origin.rstrip("/") + "/"
    self.timeout = timeout

  def get(self, name: str, version: str) -> ExtensionReleaseDescriptor:
    namespace, extension = validate_coordinate(name, version)
    url = urljoin(
      self.origin,
      f"v1/extensions/{namespace}/{extension}/releases/{version}",
    )
    try:
      response = requests.get(url, timeout=self.timeout)
      response.raise_for_status()
      release = ExtensionReleaseDescriptor.model_validate(response.json())
    except (requests.RequestException, ValueError, pydantic.ValidationError) as error:
      raise ExtensionRegistryError(
        f"Registry could not resolve {name}@{version}"
      ) from error
    if release.name != name or release.version != version:
      raise ExtensionRegistryError("Registry returned a different exact Release")
    return release


def require_python_association(
  release: ExtensionReleaseDescriptor,
) -> PythonReleaseDescriptor:
  association = release.python
  if association is None:
    raise ExtensionCompatibilityError(
      f"{release.name}@{release.version} has no Core Python Distribution"
    )
  if association.host_sdk != CORE_HOST_SDK:
    raise ExtensionCompatibilityError("Python Distribution targets another Host SDK")
  try:
    compatible = NpmSpec(association.host_sdk_version).match(Version(CORE_HOST_SDK_VERSION))
  except ValueError as error:
    raise ExtensionCompatibilityError(
      "Python Distribution declares an invalid Core Host SDK range"
    ) from error
  if not compatible:
    raise ExtensionCompatibilityError(
      f"Python Distribution does not support {CORE_HOST_SDK}@{CORE_HOST_SDK_VERSION}"
    )
  entry_point = association.entry_point
  if entry_point.group != ENTRY_POINT_GROUP:
    raise ExtensionCompatibilityError("Python Distribution entry-point group is invalid")
  if not entry_point.name or not entry_point.object or ":" not in entry_point.object:
    raise ExtensionCompatibilityError("Python Distribution entry point is invalid")
  return association


def simple_project_and_index_urls(
  origin: str,
  association: PythonReleaseDescriptor,
) -> tuple[str, str]:
  project_url = urljoin(origin.rstrip("/") + "/", association.simple_url)
  configured = urlsplit(origin)
  parsed = urlsplit(project_url)
  if (
    configured.scheme not in {"http", "https"}
    or not configured.netloc
    or configured.username is not None
    or configured.password is not None
    or configured.query
    or configured.fragment
  ):
    raise ExtensionCompatibilityError("Configured Registry origin is invalid")
  if (
    parsed.scheme != configured.scheme
    or parsed.netloc.lower() != configured.netloc.lower()
    or parsed.username is not None
    or parsed.password is not None
    or parsed.query
    or parsed.fragment
  ):
    raise ExtensionCompatibilityError("Registry Simple URL is not same-origin")
  if parsed.scheme not in {"http", "https"} or not parsed.netloc:
    raise ExtensionCompatibilityError("Registry Simple URL is not HTTP(S)")
  expected_path = f"/simple/{canonicalize_name(association.project)}/"
  if parsed.path != expected_path:
    raise ExtensionCompatibilityError(
      "Registry Simple URL does not use the declared Project path"
    )
  index_url = urlunsplit((parsed.scheme, parsed.netloc, "/simple/", "", ""))
  return project_url, index_url
