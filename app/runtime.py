"""Observable application bootstrap state."""

from dataclasses import asdict, dataclass
from enum import StrEnum
from collections.abc import Callable


class RuntimePhase(StrEnum):
  """Phases exposed by the readiness contract."""

  STARTING = "starting"
  WAITING_FOR_DATABASE = "waiting_for_database"
  READY = "ready"
  FAILED = "failed"
  STOPPING = "stopping"


@dataclass
class RuntimeStatus:
  """Mutable state owned by the application lifespan."""

  phase: RuntimePhase = RuntimePhase.STARTING
  reason: str = "runtime_bootstrap_pending"
  step: str | None = None

  @property
  def ready(self) -> bool:
    return self.phase is RuntimePhase.READY

  def set(self, phase: RuntimePhase, reason: str, *, step: str | None = None) -> None:
    self.phase = phase
    self.reason = reason
    self.step = step

  def as_dict(self) -> dict[str, str | None]:
    return asdict(self)


RUNTIME_STATUS = RuntimeStatus()

_PROCESS_RESTART_REQUESTED = False
_PROCESS_RESTART_CALLBACK: Callable[[], None] | None = None


def configure_process_restart(callback: Callable[[], None]) -> None:
  global _PROCESS_RESTART_CALLBACK
  _PROCESS_RESTART_CALLBACK = callback


def request_process_restart() -> None:
  """Ask the entrypoint to replace this process after graceful shutdown."""
  global _PROCESS_RESTART_REQUESTED
  _PROCESS_RESTART_REQUESTED = True
  if _PROCESS_RESTART_CALLBACK is not None:
    _PROCESS_RESTART_CALLBACK()


def process_restart_requested() -> bool:
  return _PROCESS_RESTART_REQUESTED
