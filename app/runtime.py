"""Observable application bootstrap state."""

from dataclasses import asdict, dataclass
from enum import StrEnum


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

  @property
  def ready(self) -> bool:
    return self.phase is RuntimePhase.READY

  def set(self, phase: RuntimePhase, reason: str) -> None:
    self.phase = phase
    self.reason = reason

  def as_dict(self) -> dict[str, str]:
    return asdict(self)


RUNTIME_STATUS = RuntimeStatus()
