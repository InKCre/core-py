"""Core facade for Distribution acquisition owned by the Extension Runtime."""

import typing
from pathlib import Path

from inkcre_extension_runtime_core_py.distribution import (
  AcquiredDistribution,
  PipDistributionConsumer as RuntimePipDistributionConsumer,
)
from inkcre_extension_runtime_core_py.modules import DistributionModules

from .release import ExtensionReleaseDescriptor, PythonReleaseDescriptor


class DistributionConsumer(typing.Protocol):
  def download(
    self,
    release: ExtensionReleaseDescriptor,
    association: PythonReleaseDescriptor,
    host_version: str,
    wheel_dir: Path,
  ) -> Path: ...

  def apply(
    self,
    extension_wheel: Path,
    release: ExtensionReleaseDescriptor,
    association: PythonReleaseDescriptor,
    host_version: str,
  ) -> AcquiredDistribution: ...


class PipDistributionConsumer:
  def __init__(self, origin: str) -> None:
    self._runtime = RuntimePipDistributionConsumer(origin)

  def download(
    self,
    release: ExtensionReleaseDescriptor,
    association: PythonReleaseDescriptor,
    host_version: str,
    wheel_dir: Path,
  ) -> Path:
    return self._runtime.download(release, association, host_version, wheel_dir)

  def apply(
    self,
    extension_wheel: Path,
    release: ExtensionReleaseDescriptor,
    association: PythonReleaseDescriptor,
    host_version: str,
  ) -> AcquiredDistribution:
    return self._runtime.apply(extension_wheel, release, association, host_version)


__all__ = [
  "AcquiredDistribution",
  "DistributionConsumer",
  "DistributionModules",
  "PipDistributionConsumer",
]
