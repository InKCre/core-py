"""Sink domain failures."""


class SinkError(RuntimeError):
  pass


class UnknownSinkTypeError(SinkError):
  pass


class SinkNotFoundError(SinkError):
  pass


class SinkStateConflictError(SinkError):
  pass


class DuplicateSinkRegistrationError(SinkError):
  pass
