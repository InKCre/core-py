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
from .agent_query import AgentQuerySink

__all__ = [
  "DuplicateSinkRegistrationError",
  "SinkBase",
  "SinkError",
  "SinkManager",
  "AgentQuerySink",
  "MCPSink",
  "SinkNotFoundError",
  "SinkStateConflictError",
  "UnknownSinkTypeError",
]
