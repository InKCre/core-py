class ExtensionHostError(RuntimeError):
  """Base error for the Core Extension Host."""


class ExtensionNotInstalledError(ExtensionHostError):
  pass


class ExtensionStateConflictError(ExtensionHostError):
  pass


class ExtensionRegistryError(ExtensionHostError):
  pass


class ExtensionCompatibilityError(ExtensionHostError):
  pass


class ExtensionAcquisitionError(ExtensionHostError):
  pass


class ExtensionEntryPointError(ExtensionHostError):
  pass


class ExtensionRuntimeError(ExtensionHostError):
  pass


class ExtensionRestartRequiredError(ExtensionStateConflictError):
  pass
