"""One Core Extension Host over Registry-native Python Distributions."""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
import typing

import fastapi
from inkcre_extension_runtime_core_py import EmptyConfig
from inkcre_extension_runtime_core_py import ExtensionBase as RuntimeExtensionBase
import pydantic
import sqlmodel

from app.business.peer import PeerManager
from app.schemas.extension import (
  DisableExtensionCommand,
  EnableExtensionCommand,
  ExtensionManagementCommand,
  PatchExtensionConfigCommand,
)
from app.schemas.peer import PeerProtocolRequest, PeerProtocolResponse, PeerRef
from app.settings import settings
from libs.obsrv.main import get_logger

from .distribution import (
  AcquiredDistribution,
  DistributionConsumer,
  DistributionModules,
  PipDistributionConsumer,
)
from .config import resolve_extension_registry_origin
from .errors import (
  ExtensionCompatibilityError,
  ExtensionHostError,
  ExtensionNotInstalledError,
  ExtensionRestartRequiredError,
  ExtensionRuntimeError,
  ExtensionStateConflictError,
)
from .release import (
  PythonReleaseDescriptor,
  RegistryReleaseClient,
  ReleaseState,
  ReleaseResolver,
  require_python_association,
  validate_coordinate,
)
from .runtime import (
  PublicHTTPRoute,
  ExtensionRuntimeClaim,
  ExtensionRuntimeClaimConflictError,
)
from .state import ExtensionStore, InstalledExtension, SQLExtensionStore


LOGGER = get_logger().getChild(__name__)
EXTENSION_MANAGEMENT_CAPABILITY = "core.extension.management.v1"


class ExtensionDelegationError(RuntimeError):
  """The selected Peer did not return the Extension management contract."""


class ExtensionBase(RuntimeExtensionBase, ext_id="_facade"):
  """Core import facade retaining the established one-parameter type spelling."""

  config: typing.Any

  @classmethod
  def __class_getitem__(cls, _item: typing.Any) -> type[ExtensionBase]:
    return cls

  @classmethod
  def on_start(cls, app: typing.Any) -> None:
    super().on_start(app)
    cls.config = cls.get_config()

  @classmethod
  def update_config(cls, value: typing.Any) -> typing.Any:
    config = super().update_config(value)
    cls.config = config
    return config

  @classmethod
  def mutate_config_and_state(cls, transform: typing.Any) -> tuple[typing.Any, typing.Any]:
    config, state = super().mutate_config_and_state(transform)
    cls.config = config
    return config, state

  @classmethod
  def validate_config(cls, config: dict[str, typing.Any]) -> typing.Any:
    return cls.__configcls__.model_validate(config)


@dataclass
class _ActiveExtensionModel:
  """Bind the Core store to the Runtime's rich active-record interface."""

  name: str
  config: dict[str, typing.Any]
  store: ExtensionStore
  persist_schema: bool = True

  def _refresh(self) -> _ActiveExtensionModel:
    self.config = self.store.read_config(self.name)
    return self

  def update_config(self, config: dict[str, typing.Any]) -> _ActiveExtensionModel:
    self.store.update_config(self.name, config)
    return self._refresh()

  def update_config_schema(self, schema: dict[str, typing.Any]) -> _ActiveExtensionModel:
    if self.persist_schema:
      self.store.update_config_schema(self.name, schema)
    return self._refresh()

  def read_state(self) -> dict[str, typing.Any]:
    return self.store.read_state(self.name)

  def mutate_state(
    self,
    transform: typing.Callable[[dict[str, typing.Any]], dict[str, typing.Any]],
  ) -> dict[str, typing.Any]:
    return self.store.mutate_state(self.name, transform)

  def mutate_config_and_state(
    self,
    transform: typing.Callable[
      [dict[str, typing.Any], dict[str, typing.Any]],
      tuple[dict[str, typing.Any], dict[str, typing.Any]],
    ],
  ) -> tuple[dict[str, typing.Any], dict[str, typing.Any]]:
    result = self.store.mutate_config_and_state(self.name, transform)
    self._refresh()
    return result


@dataclass
class RunningExtension:
  name: str
  version: str
  association: PythonReleaseDescriptor
  acquired: AcquiredDistribution
  extension_class: type[ExtensionBase]
  modules: DistributionModules
  claim: ExtensionRuntimeClaim


class ExtensionHost:
  """Canonical install/config/enable/disable/uninstall facade for Core."""

  def __init__(
    self,
    *,
    store: ExtensionStore | None = None,
    release_client: ReleaseResolver | None = None,
    distribution_consumer: DistributionConsumer | None = None,
    registry_origin_resolver: typing.Callable[[], str] | None = None,
  ) -> None:
    self.store = store or SQLExtensionStore()
    self.release_client = release_client
    self.distribution_consumer = distribution_consumer
    self.registry_origin_resolver = (
      registry_origin_resolver or resolve_extension_registry_origin
    )
    self.running: dict[str, RunningExtension] = {}
    self.fastapi_app: fastapi.FastAPI | None = None
    self._loaded_versions: dict[str, str] = {}
    self._runtime_lock = asyncio.Lock()

  def list(self) -> tuple[InstalledExtension, ...]:
    return self.store.list()

  async def manage(
    self,
    command: ExtensionManagementCommand,
    *,
    route_to_peer: PeerRef,
  ) -> InstalledExtension:
    """Execute one Extension command on one exact Peer."""
    if route_to_peer == PeerManager.get_current_peer_ref():
      return await self.manage_local(command)

    request = PeerProtocolRequest(body=command.model_dump(mode="json"))
    result = await PeerManager.delegate(
      EXTENSION_MANAGEMENT_CAPABILITY,
      typing.cast(
        typing.Any,
        request.model_dump(mode="json", exclude_unset=True),
      ),
      route_to_peer=route_to_peer,
    )
    try:
      response = PeerProtocolResponse.model_validate(result)
      if response.status != 200 or "body" not in response.model_fields_set:
        raise ExtensionDelegationError(
          f"Extension management Peer returned HTTP {response.status}"
        )
      return InstalledExtension.model_validate(response.body)
    except pydantic.ValidationError as error:
      raise ExtensionDelegationError(
        "Extension management Peer returned an invalid response"
      ) from error

  async def manage_local(
    self,
    command: ExtensionManagementCommand,
  ) -> InstalledExtension:
    """Execute one already-validated command without entering delegation."""
    if isinstance(command, EnableExtensionCommand):
      return await self.enable(command.extension)
    if isinstance(command, DisableExtensionCommand):
      return await self.disable(command.extension)
    if isinstance(command, PatchExtensionConfigCommand):
      return self.patch_config(command.extension, command.patch)
    typing.assert_never(command)

  def get(self, name: str) -> InstalledExtension:
    validate_coordinate(name)
    state = self.store.get(name)
    if state is None:
      raise ExtensionNotInstalledError(f"{name} is not installed")
    return state

  def _resolve(
    self,
    name: str,
    version: str,
    *,
    allow_yanked: bool,
    release_client: ReleaseResolver,
  ):
    release = release_client.get(name, version)
    if release.state is ReleaseState.yanked and allow_yanked:
      LOGGER.warning("Using yanked exact installed Release %s@%s", name, version)
    elif release.state is not ReleaseState.published:
      raise ExtensionCompatibilityError(
        f"{name}@{version} is not available for this operation"
      )
    association = require_python_association(release)
    return release, association

  def install(self, name: str, version: str) -> InstalledExtension:
    validate_coordinate(name, version)
    existing = self.store.get(name)
    if existing is not None and existing.version == version:
      return existing
    loaded_version = self._loaded_versions.get(name)
    if loaded_version is not None and loaded_version != version:
      raise ExtensionRestartRequiredError(
        f"{name} {loaded_version} was already imported; restart before installing {version}"
      )
    release_client, _ = self._operation_consumers()
    release, _ = self._resolve(
      name,
      version,
      allow_yanked=False,
      release_client=release_client,
    )
    return self.store.install(name, version, release.nickname)

  def uninstall(self, name: str) -> None:
    validate_coordinate(name)
    if name in self.running:
      raise ExtensionStateConflictError(f"Cannot uninstall running Extension {name}")
    self.store.uninstall(name)

  def update_config(
    self,
    name: str,
    config: dict[str, typing.Any],
  ) -> InstalledExtension:
    state = self.get(name)
    running = self.running.get(name)
    if running is None:
      return self.store.update_config(name, config)
    config_class = typing.cast(
      type[sqlmodel.SQLModel],
      getattr(running.extension_class, "__configcls__"),
    )
    validated = config_class(**config)
    running.extension_class.update_config(validated)
    return self.get(name)

  def patch_config(
    self,
    name: str,
    patch: dict[str, typing.Any],
  ) -> InstalledExtension:
    """Apply one shallow config patch through the canonical update path."""
    current = self.get(name)
    return self.update_config(name, {**current.config, **patch})

  def _operation_consumers(
    self,
  ) -> tuple[ReleaseResolver, DistributionConsumer]:
    if self.release_client is not None and self.distribution_consumer is not None:
      return self.release_client, self.distribution_consumer
    origin = self.registry_origin_resolver()
    release_client = self.release_client or RegistryReleaseClient(
      origin,
      settings.extension_registry_timeout_seconds,
    )
    distribution_consumer = self.distribution_consumer or PipDistributionConsumer(origin)
    return release_client, distribution_consumer

  def _acquire(self, state: InstalledExtension):
    release_client, distribution_consumer = self._operation_consumers()
    release, association = self._resolve(
      state.name,
      state.version,
      allow_yanked=True,
      release_client=release_client,
    )
    acquired = distribution_consumer.acquire(release, association)
    return association, acquired

  async def _start(
    self,
    app: fastapi.FastAPI,
    state: InstalledExtension,
  ) -> RunningExtension:
    existing = self.running.get(state.name)
    if existing is not None:
      if existing.version != state.version:
        raise ExtensionRestartRequiredError(
          f"A different Release of {state.name} is already running"
        )
      return existing

    association, acquired = await asyncio.to_thread(self._acquire, state)
    return await self._start_acquired(app, state, association, acquired)

  async def _start_acquired(
    self,
    app: fastapi.FastAPI,
    state: InstalledExtension,
    association: PythonReleaseDescriptor,
    acquired: AcquiredDistribution,
    *,
    persist_schema: bool = True,
  ) -> RunningExtension:
    try:
      claim = ExtensionRuntimeClaim.acquire(association.entry_point.name)
    except ExtensionRuntimeClaimConflictError as error:
      raise ExtensionStateConflictError(str(error)) from error
    try:
      modules = DistributionModules(acquired)
    except Exception:
      claim.release()
      raise
    extension_class: type[ExtensionBase] | None = None

    try:
      extension_class = typing.cast(type[ExtensionBase], modules.load(ExtensionBase))
      if extension_class.__extid__ != association.entry_point.name:
        raise ExtensionCompatibilityError(
          "ExtensionBase identity differs from the declared entry point"
        )
      extension_class.bind(
        _ActiveExtensionModel(
          name=state.name,
          config=dict(state.config),
          store=self.store,
          persist_schema=persist_schema,
        )
      )
      extension_class.on_start(app)
      modules.assert_origins()
    except Exception:
      if extension_class is not None:
        with contextlib.suppress(Exception):
          await extension_class.on_close()
        with contextlib.suppress(Exception):
          extension_class.unpublish()
        with contextlib.suppress(Exception):
          extension_class.unbind()
        with contextlib.suppress(Exception):
          extension_class.release_runtime()
      with contextlib.suppress(Exception):
        modules.abort()
      claim.release()
      raise

    running = RunningExtension(
      name=state.name,
      version=state.version,
      association=association,
      acquired=acquired,
      extension_class=extension_class,
      modules=modules,
      claim=claim,
    )
    self.running[state.name] = running
    self._loaded_versions[state.name] = state.version
    return running

  async def _stop(self, running: RunningExtension) -> None:
    await running.extension_class.on_close()
    running.extension_class.unpublish()
    running.extension_class.unbind()
    running.modules.unload()
    running.extension_class.release_runtime()
    running.claim.release()
    self.running.pop(running.name, None)

  async def _force_stop(self, running: RunningExtension) -> typing.List[Exception]:
    failures: list[Exception] = []
    try:
      await running.extension_class.on_close()
    except Exception as error:
      failures.append(error)
    try:
      running.extension_class.unpublish()
    except Exception as error:
      failures.append(error)
    try:
      running.extension_class.unbind()
    except Exception as error:
      failures.append(error)
    try:
      running.modules.abort()
    except Exception as error:
      failures.append(error)
    finally:
      running.extension_class.release_runtime()
      running.claim.release()
      self.running.pop(running.name, None)
    return failures

  async def enable(
    self,
    name: str,
    *,
    app: fastapi.FastAPI | None = None,
  ) -> InstalledExtension:
    validate_coordinate(name)
    runtime_app = app or self.fastapi_app
    if runtime_app is None:
      raise ExtensionRuntimeError("FastAPI app is required to enable an Extension")
    self.fastapi_app = runtime_app
    peer_id = PeerManager.get_current_peer_ref()
    async with self._runtime_lock:
      state = self.get(name)
      running = await self._start(runtime_app, state)
      if peer_id in state.enabled:
        return state
      try:
        persisted = self.store.set_peer_enabled(name, peer_id, True)
      except Exception as persistence_error:
        failures = await self._force_stop(running)
        if failures:
          raise ExceptionGroup(
            "Enable persistence and runtime compensation failed",
            [persistence_error, *failures],
          ) from persistence_error
        raise
      if persisted.version == running.version:
        if running.extension_class.peer_inbounds():
          PeerManager.refresh_self(settings.peer_lease_ttl_seconds)
        return persisted

      conflict = ExtensionStateConflictError(
        f"{name} changed from {running.version} to {persisted.version} during enable"
      )
      compensation_failures: list[Exception] = []
      try:
        self.store.set_peer_enabled(name, peer_id, False)
      except Exception as error:
        compensation_failures.append(error)
      compensation_failures.extend(await self._force_stop(running))
      if compensation_failures:
        raise ExceptionGroup(
          "Concurrent version change and enable compensation failed",
          [conflict, *compensation_failures],
        ) from conflict
      raise conflict

  async def disable(self, name: str) -> InstalledExtension:
    validate_coordinate(name)
    peer_id = PeerManager.get_current_peer_ref()
    async with self._runtime_lock:
      state = self.get(name)
      if peer_id not in state.enabled:
        return state
      running = self.running.get(name)
      published_peer_inbounds = (
        bool(running.extension_class.peer_inbounds()) if running is not None else False
      )
      if running is not None:
        await self._stop(running)
      try:
        persisted = self.store.set_peer_enabled(name, peer_id, False)
        if published_peer_inbounds:
          PeerManager.refresh_self(settings.peer_lease_ttl_seconds)
        return persisted
      except Exception as persistence_error:
        if running is None:
          raise
        runtime_app = self.fastapi_app
        if runtime_app is None:
          raise ExtensionRuntimeError(
            "FastAPI app is unavailable for disable compensation"
          ) from persistence_error
        try:
          await self._start_acquired(
            runtime_app,
            state,
            running.association,
            running.acquired,
            persist_schema=False,
          )
        except Exception as restart_error:
          raise ExceptionGroup(
            "Disable persistence and runtime restart failed",
            [persistence_error, restart_error],
          ) from persistence_error
        raise

  async def start_enabled(self, app: fastapi.FastAPI) -> None:
    """Cold-restore exact enabled intent; failures never rewrite enabled[]."""
    self.fastapi_app = app
    peer_id = PeerManager.get_current_peer_ref()
    async with self._runtime_lock:
      for state in self.store.list():
        if peer_id not in state.enabled:
          continue
        try:
          await self._start(app, state)
        except Exception:
          LOGGER.exception("Cold restore failed for %s", state.name)

  async def close_running(self) -> None:
    failures: list[Exception] = []
    async with self._runtime_lock:
      for running in tuple(self.running.values()):
        try:
          await self._stop(running)
        except Exception as error:
          failures.append(error)
    if len(failures) == 1:
      raise failures[0]
    if failures:
      raise ExceptionGroup("Extension shutdown failed", failures)


EXTENSION_HOST = ExtensionHost()


__all__ = [
  "EXTENSION_MANAGEMENT_CAPABILITY",
  "EXTENSION_HOST",
  "EmptyConfig",
  "ExtensionBase",
  "ExtensionDelegationError",
  "ExtensionHost",
  "ExtensionHostError",
  "InstalledExtension",
  "PublicHTTPRoute",
]
