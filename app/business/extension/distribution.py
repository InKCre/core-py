"""Core facade for Distribution acquisition owned by the Extension Runtime."""

import typing

from inkcre_extension_runtime_core_py.distribution import (
  AcquiredDistribution,
  PipDistributionConsumer as RuntimePipDistributionConsumer,
)
from inkcre_extension_runtime_core_py.modules import DistributionModules

from app.version import CORE_VERSION

from .release import ExtensionReleaseDescriptor, PythonReleaseDescriptor


class DistributionConsumer(typing.Protocol):
  def acquire(
    self,
    release: ExtensionReleaseDescriptor,
    association: PythonReleaseDescriptor,
  ) -> AcquiredDistribution: ...


class PipDistributionConsumer:
  def __init__(self, origin: str) -> None:
    self._runtime = RuntimePipDistributionConsumer(origin)

  def acquire(
    self,
    release: ExtensionReleaseDescriptor,
    association: PythonReleaseDescriptor,
  ) -> AcquiredDistribution:
    return self._runtime.acquire(release, association, CORE_VERSION)


__all__ = [
  "AcquiredDistribution",
  "DistributionConsumer",
  "DistributionModules",
  "PipDistributionConsumer",
]
