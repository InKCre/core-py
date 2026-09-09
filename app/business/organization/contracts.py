"""Stable failures at the Organization capability boundary."""


class OrganizationError(RuntimeError):
  """Base failure at the Organization capability boundary."""


class OrganizationBlockNotFoundError(OrganizationError):
  pass


class OrganizationNotConfiguredError(OrganizationError):
  pass


class OrganizationAgentNotFoundError(OrganizationError):
  pass


class OrganizationExecutionError(OrganizationError):
  pass


class OrganizationDelegationError(OrganizationError):
  pass
