"""Core facade for the independently released Runtime error taxonomy."""

from inkcre_extension_runtime_core_py.errors import (
  ExtensionAcquisitionError,
  ExtensionCompatibilityError,
  ExtensionEntryPointError,
  ExtensionLifecycleError,
  ExtensionNotInstalledError,
  ExtensionRegistryError,
  ExtensionRuntimeError,
  ExtensionStateConflictError,
)

ExtensionHostError = ExtensionRuntimeError


class ExtensionRestartRequiredError(ExtensionStateConflictError):
  """The loaded Distribution can only be replaced after process restart."""


class ExtensionEnvironmentApplicationRequiredError(ExtensionStateConflictError):
  """The selected exact Python release is absent from this Peer environment."""


__all__ = [
  "ExtensionAcquisitionError",
  "ExtensionCompatibilityError",
  "ExtensionEntryPointError",
  "ExtensionEnvironmentApplicationRequiredError",
  "ExtensionHostError",
  "ExtensionLifecycleError",
  "ExtensionNotInstalledError",
  "ExtensionRegistryError",
  "ExtensionRestartRequiredError",
  "ExtensionRuntimeError",
  "ExtensionStateConflictError",
]
