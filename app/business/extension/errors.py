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


__all__ = [
  "ExtensionAcquisitionError",
  "ExtensionCompatibilityError",
  "ExtensionEntryPointError",
  "ExtensionHostError",
  "ExtensionLifecycleError",
  "ExtensionNotInstalledError",
  "ExtensionRegistryError",
  "ExtensionRestartRequiredError",
  "ExtensionRuntimeError",
  "ExtensionStateConflictError",
]
