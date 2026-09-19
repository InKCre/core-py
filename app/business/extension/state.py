"""Semantic deployment-state port for the canonical extensions relation."""

from __future__ import annotations

from collections.abc import Callable
import typing
import uuid

import pydantic

from app.persistence.extension.uow import extension_uow
from app.schemas.extension import ExtensionModel

from .errors import ExtensionNotInstalledError, ExtensionStateConflictError


class InstalledExtension(pydantic.BaseModel):
  """Stable Host-facing projection; SQLModel and table details remain private."""

  model_config = pydantic.ConfigDict(frozen=True)

  name: str
  version: str
  enabled: tuple[uuid.UUID, ...] = ()
  nickname: str | None = None
  config: dict[str, typing.Any] = pydantic.Field(default_factory=dict)
  # Extension-produced state may contain credentials. It remains available to
  # the in-process Host SDK but is never serialized through generic management.
  state: dict[str, typing.Any] = pydantic.Field(default_factory=dict, exclude=True)
  config_schema: dict[str, typing.Any] | None = None


StateMutation: typing.TypeAlias = Callable[[dict[str, typing.Any]], dict[str, typing.Any]]
ConfigStateMutation: typing.TypeAlias = Callable[
  [dict[str, typing.Any], dict[str, typing.Any]],
  tuple[dict[str, typing.Any], dict[str, typing.Any]],
]


class ExtensionStore(typing.Protocol):
  async def list(self) -> tuple[InstalledExtension, ...]: ...

  async def get(self, name: str) -> InstalledExtension | None: ...

  async def install(self, name: str, version: str, nickname: str) -> InstalledExtension: ...

  async def uninstall(self, name: str) -> None: ...

  async def read_config(self, name: str) -> dict[str, typing.Any]: ...

  async def update_config(
    self, name: str, config: dict[str, typing.Any]
  ) -> InstalledExtension: ...

  async def read_state(self, name: str) -> dict[str, typing.Any]: ...

  async def mutate_state(
    self, name: str, transform: StateMutation
  ) -> dict[str, typing.Any]: ...

  async def mutate_config_and_state(
    self,
    name: str,
    transform: ConfigStateMutation,
  ) -> tuple[dict[str, typing.Any], dict[str, typing.Any]]: ...

  async def update_config_schema(
    self, name: str, schema: dict[str, typing.Any]
  ) -> InstalledExtension: ...

  async def set_peer_enabled(
    self, name: str, peer_id: uuid.UUID, enabled: bool
  ) -> InstalledExtension: ...


class ExtensionStateService:
  """Transactional adapter over the one canonical deployment relation."""

  @staticmethod
  def _state(model: ExtensionModel) -> InstalledExtension:
    return InstalledExtension(
      name=model.name,
      version=model.version,
      enabled=tuple(model.enabled),
      nickname=model.nickname,
      config=dict(model.config),
      state=dict(model.state),
      config_schema=(
        dict(model.config_schema) if model.config_schema is not None else None
      ),
    )

  async def list(self) -> tuple[InstalledExtension, ...]:
    async with extension_uow() as repository:
      rows = await repository.list()
      return tuple(self._state(row) for row in rows)

  async def get(self, name: str) -> InstalledExtension | None:
    async with extension_uow() as repository:
      row = await repository.get(name)
      return self._state(row) if row is not None else None

  async def install(self, name: str, version: str, nickname: str) -> InstalledExtension:
    async with extension_uow() as repository:
      locked = await repository.try_install_lock(name)
      if not locked:
        raise ExtensionStateConflictError(
          f"Another install operation for {name} is already in progress"
        )
      row = await repository.get(name, lock=True)
      if row is None:
        row = ExtensionModel(
          name=name,
          version=version,
          enabled=[],
          nickname=nickname,
          config={},
          state={},
          config_schema=None,
        )
      elif row.version != version:
        if row.enabled:
          raise ExtensionStateConflictError(
            f"Cannot change {name} while one or more peers are enabled"
          )
        if row.state:
          raise ExtensionStateConflictError(
            f"Cannot change {name} while Extension state is not empty"
          )
        row.version = version
        row.nickname = nickname
        row.config_schema = None
      else:
        row.nickname = nickname
      await repository.save(row)
      return self._state(row)

  async def uninstall(self, name: str) -> None:
    async with extension_uow() as repository:
      row = await repository.get(name, lock=True)
      if row is None:
        raise ExtensionNotInstalledError(f"{name} is not installed")
      if row.enabled:
        raise ExtensionStateConflictError(
          f"Cannot uninstall {name} while one or more peers are enabled"
        )
      await repository.delete(row)

  async def _update_json(
    self,
    name: str,
    field: typing.Literal["config", "config_schema"],
    value: dict[str, typing.Any],
  ) -> InstalledExtension:
    async with extension_uow() as repository:
      row = await repository.get(name)
      if row is None:
        raise ExtensionNotInstalledError(f"{name} is not installed")
      setattr(row, field, value)
      await repository.save(row)
      return self._state(row)

  async def update_config(
    self, name: str, config: dict[str, typing.Any]
  ) -> InstalledExtension:
    return await self._update_json(name, "config", config)

  async def read_config(self, name: str) -> dict[str, typing.Any]:
    state = await self.get(name)
    if state is None:
      raise ExtensionNotInstalledError(f"{name} is not installed")
    return dict(state.config)

  async def read_state(self, name: str) -> dict[str, typing.Any]:
    state = await self.get(name)
    if state is None:
      raise ExtensionNotInstalledError(f"{name} is not installed")
    return dict(state.state)

  async def mutate_state(
    self,
    name: str,
    transform: StateMutation,
  ) -> dict[str, typing.Any]:
    async with extension_uow() as repository:
      row = await repository.get(name, lock=True)
      if row is None:
        raise ExtensionNotInstalledError(f"{name} is not installed")
      row.state = transform(dict(row.state))
      await repository.save(row)
      return dict(row.state)

  async def mutate_config_and_state(
    self,
    name: str,
    transform: ConfigStateMutation,
  ) -> tuple[dict[str, typing.Any], dict[str, typing.Any]]:
    async with extension_uow() as repository:
      row = await repository.get(name, lock=True)
      if row is None:
        raise ExtensionNotInstalledError(f"{name} is not installed")
      config, state = transform(dict(row.config), dict(row.state))
      row.config = config
      row.state = state
      await repository.save(row)
      return dict(row.config), dict(row.state)

  async def update_config_schema(
    self, name: str, schema: dict[str, typing.Any]
  ) -> InstalledExtension:
    return await self._update_json(name, "config_schema", schema)

  async def set_peer_enabled(
    self, name: str, peer_id: uuid.UUID, enabled: bool
  ) -> InstalledExtension:
    """Use the shared atomic RPC; Core never performs array read-modify-write."""
    async with extension_uow() as repository:
      row = await repository.set_peer_enabled(name, peer_id, enabled)
      if row is None:
        raise ExtensionNotInstalledError(f"{name} is not installed")
      return InstalledExtension.model_validate(dict(row))
