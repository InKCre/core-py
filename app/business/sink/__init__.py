"""Sink domain."""

from .base import SinkBase
from .errors import (
  DuplicateSinkRegistrationError,
  SinkError,
  SinkNotFoundError,
  SinkStateConflictError,
  UnknownSinkTypeError,
)
from .main import SinkManager
from .mcp import MCPSink

__all__ = [
  "DuplicateSinkRegistrationError",
  "SinkBase",
  "SinkError",
  "SinkManager",
  "MCPSink",
  "SinkNotFoundError",
  "SinkStateConflictError",
  "UnknownSinkTypeError",
]
