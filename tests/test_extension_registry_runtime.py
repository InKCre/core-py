"""Focused tests for the canonical native Core Extension Host."""

from __future__ import annotations

import asyncio
import typing
import uuid

import fastapi
import pytest
import sqlmodel

import app.business.extension.main as host_module
from app.business.extension.distribution import AcquiredDistribution
from app.business.extension.errors import (
  ExtensionCompatibilityError,
  ExtensionRestartRequiredError,
  ExtensionStateConflictError,
)
from app.business.extension.main import ExtensionBase, ExtensionHost, PublicHTTPRoute
from app.business.extension.release import (
  EntryPointDescriptor,
  ExtensionReleaseDescriptor,
  PythonReleaseDescriptor,
  require_python_association,
  simple_project_and_index_urls,
)
from app.business.extension.state import InstalledExtension
from app.business.extension.runtime import ExtensionRuntimeClaim, PublicHTTPRouteClaim
from app.business.client import ClientManager


PEER_ID = uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
NAME = "inkcre/fixture"


class FixtureConfig(sqlmodel.SQLModel):
  value: int = 1


class FixtureRuntimeState(sqlmodel.SQLModel):
  counter: int = 0


class FixtureExtension(
  ExtensionBase,
  ext_id="fixture",
  config_cls=FixtureConfig,
  state_cls=FixtureRuntimeState,
):
  fail_close = False

  @classmethod
  def _register_apis(cls, router: fastapi.APIRouter) -> None:
    @router.get("/status")
    def status():
      return {"ok": True}

    @router.get("/callback")
    def callback():
      return {"ok": True}

  @classmethod
  def public_http_routes(cls):
    return (PublicHTTPRoute(method="GET", path="/callback"),)

  @classmethod
  async def on_close(cls) -> None:
    if cls.fail_close:
      raise RuntimeError("close failed")
    await super().on_close()


def association(host_sdk_version: str = "^0.1.0") -> PythonReleaseDescriptor:
  return PythonReleaseDescriptor(
    project="inkcre-extension-fixture",
    simple_url="/simple/inkcre-extension-fixture/",
    host_sdk="core-py",
    host_sdk_version=host_sdk_version,
    entry_point=EntryPointDescriptor(
      group="inkcre.core.extensions",
      name="fixture",
      object="extensions.fixture:FixtureExtension",
    ),
  )


def release(*, state: str = "published", version: str = "1.0.0"):
  return ExtensionReleaseDescriptor(
    name=NAME,
    nickname="Fixture",
    version=version,
    state=state,
    python=association(),
  )


class FakeStore:
  def __init__(self, state: InstalledExtension | None = None) -> None:
    self.state = state
    self.runtime_state: dict[str, typing.Any] = {}
    self.set_calls: list[tuple[str, uuid.UUID, bool]] = []
    self.fail_set = False
    self.version_on_enable: str | None = None

  def list(self):
    return (self.state,) if self.state is not None else ()

  def get(self, name: str):
    return self.state if self.state is not None and self.state.name == name else None

  def install(self, name: str, version: str, nickname: str):
    if self.state is not None and self.state.version != version and self.state.enabled:
      raise ExtensionStateConflictError("enabled")
    self.state = InstalledExtension(
      name=name,
      version=version,
      nickname=nickname,
      enabled=self.state.enabled if self.state is not None else (),
      config=self.state.config if self.state is not None else {},
    )
    return self.state

  def uninstall(self, name: str):
    self.state = None

  def update_config(self, name: str, config: dict):
    assert self.state is not None
    self.state = self.state.model_copy(update={"config": config})
    return self.state

  def read_config(self, name: str):
    assert self.state is not None
    return dict(self.state.config)

  def read_state(self, name: str):
    return dict(self.runtime_state)

  def mutate_state(self, name: str, transform):
    self.runtime_state = transform(dict(self.runtime_state))
    return dict(self.runtime_state)

  def mutate_config_and_state(self, name: str, transform):
    assert self.state is not None
    config, state = transform(dict(self.state.config), dict(self.runtime_state))
    self.state = self.state.model_copy(update={"config": config})
    self.runtime_state = state
    return dict(config), dict(state)

  def update_config_schema(self, name: str, schema: dict):
    assert self.state is not None
    self.state = self.state.model_copy(update={"config_schema": schema})
    return self.state

  def set_peer_enabled(self, name: str, peer_id: uuid.UUID, enabled: bool):
    self.set_calls.append((name, peer_id, enabled))
    if self.fail_set:
      raise RuntimeError("RPC failed")
    assert self.state is not None
    if enabled and self.version_on_enable is not None:
      self.state = self.state.model_copy(update={"version": self.version_on_enable})
    peers = set(self.state.enabled)
    if enabled:
      peers.add(peer_id)
    else:
      peers.discard(peer_id)
    self.state = self.state.model_copy(update={"enabled": tuple(sorted(peers))})
    return self.state


class FakeReleaseClient:
  def __init__(self, descriptor: ExtensionReleaseDescriptor) -> None:
    self.descriptor = descriptor

  def get(self, name: str, version: str) -> ExtensionReleaseDescriptor:
    assert (name, version) == (self.descriptor.name, self.descriptor.version)
    return self.descriptor


class FakeConsumer:
  def __init__(self) -> None:
    self.calls = 0

  def acquire(
    self,
    release: ExtensionReleaseDescriptor,
    association: PythonReleaseDescriptor,
  ) -> AcquiredDistribution:
    self.calls += 1
    return typing.cast(AcquiredDistribution, object())


class FakeModules:
  fail_unload = False

  def __init__(self, acquired) -> None:
    self.aborted = False

  def load(self, extension_base):
    return FixtureExtension

  def assert_origins(self):
    return None

  def unload(self):
    if self.fail_unload:
      raise RuntimeError("unload failed")
    self.aborted = True

  def abort(self):
    self.aborted = True


@pytest.fixture(autouse=True)
def clean_runtime(monkeypatch):
  FixtureExtension.fail_close = False
  FixtureExtension.unpublish()
  FixtureExtension.release_runtime()
  FakeModules.fail_unload = False
  with ExtensionRuntimeClaim._lock:
    ExtensionRuntimeClaim._owners.clear()
  with PublicHTTPRouteClaim._lock:
    PublicHTTPRouteClaim._owners.clear()
  monkeypatch.setattr(host_module, "DistributionModules", FakeModules)
  monkeypatch.setattr(ClientManager, "get_current_client_id", lambda: PEER_ID)
  yield
  FixtureExtension.fail_close = False
  FixtureExtension.unpublish()
  FixtureExtension.release_runtime()
  with ExtensionRuntimeClaim._lock:
    ExtensionRuntimeClaim._owners.clear()
  with PublicHTTPRouteClaim._lock:
    PublicHTTPRouteClaim._owners.clear()


def make_host(state: InstalledExtension, descriptor=None):
  store = FakeStore(state)
  consumer = FakeConsumer()
  host = ExtensionHost(
    store=store,
    release_client=FakeReleaseClient(descriptor or release()),
    distribution_consumer=consumer,
  )
  return host, store, consumer


def test_enable_starts_before_atomic_enabled_rpc_and_rolls_back_on_rpc_failure():
  state = InstalledExtension(name=NAME, version="1.0.0")
  host, store, _ = make_host(state)
  store.fail_set = True
  app = fastapi.FastAPI()
  original_routes = len(app.routes)

  with pytest.raises(RuntimeError, match="RPC failed"):
    asyncio.run(host.enable(NAME, app=app))

  assert store.state is not None and store.state.enabled == ()
  assert store.set_calls == [(NAME, PEER_ID, True)]
  assert host.running == {}
  assert len(app.routes) == original_routes
  assert not PublicHTTPRouteClaim.permits("GET", "/fixture/callback")


def test_public_http_route_claim_follows_runtime_publication_lifecycle():
  state = InstalledExtension(name=NAME, version="1.0.0")
  host, _, _ = make_host(state)

  asyncio.run(host.enable(NAME, app=fastapi.FastAPI()))
  assert PublicHTTPRouteClaim.permits("GET", "/fixture/callback")
  assert not PublicHTTPRouteClaim.permits("POST", "/fixture/callback")

  asyncio.run(host.disable(NAME))
  assert not PublicHTTPRouteClaim.permits("GET", "/fixture/callback")


def test_extension_facing_config_and_state_api_reads_fresh_and_persists_immediately():
  state = InstalledExtension(name=NAME, version="1.0.0")
  host, store, _ = make_host(state)
  asyncio.run(host.enable(NAME, app=fastapi.FastAPI()))
  assert store.state is not None
  store.state = store.state.model_copy(update={"config": {"value": 7}})

  assert FixtureExtension.get_config().value == 7
  updated = FixtureExtension.update_config({"value": 9})
  runtime_state = typing.cast(
    FixtureRuntimeState,
    FixtureExtension.mutate_state(
      lambda current: FixtureRuntimeState(
        counter=typing.cast(FixtureRuntimeState, current).counter + 1
      )
    ),
  )

  assert updated.value == 9
  assert store.state.config == {"value": 9}
  assert runtime_state.counter == 1
  assert store.runtime_state == {"counter": 1}
  asyncio.run(host.disable(NAME))


def test_existing_exact_yanked_release_can_cold_restore_without_mutating_intent():
  state = InstalledExtension(name=NAME, version="1.0.0", enabled=(PEER_ID,))
  host, store, consumer = make_host(state, release(state="yanked"))

  asyncio.run(host.start_enabled(fastapi.FastAPI()))

  assert NAME in host.running
  assert store.set_calls == []
  assert consumer.calls == 1


def test_concurrent_version_change_compensates_enabled_and_started_runtime():
  state = InstalledExtension(name=NAME, version="1.0.0")
  host, store, _ = make_host(state)
  store.version_on_enable = "2.0.0"

  with pytest.raises(ExtensionStateConflictError, match="changed from"):
    asyncio.run(host.enable(NAME, app=fastapi.FastAPI()))

  assert store.set_calls == [
    (NAME, PEER_ID, True),
    (NAME, PEER_ID, False),
  ]
  assert store.state is not None
  assert store.state.version == "2.0.0"
  assert store.state.enabled == ()
  assert host.running == {}


def test_runtime_claim_blocks_cross_namespace_package_collision_until_release():
  first_name = "inkcre/fixture"
  second_name = "other/fixture"
  first_state = InstalledExtension(name=first_name, version="1.0.0")
  second_state = InstalledExtension(name=second_name, version="1.0.0")
  first_descriptor = release().model_copy(update={"name": first_name})
  second_descriptor = release().model_copy(update={"name": second_name})
  first, _, _ = make_host(first_state, first_descriptor)
  second, second_store, _ = make_host(second_state, second_descriptor)
  first_app = fastapi.FastAPI()

  asyncio.run(first.enable(first_name, app=first_app))
  with pytest.raises(ExtensionStateConflictError, match="canonical module"):
    asyncio.run(second.enable(second_name, app=fastapi.FastAPI()))
  assert second.running == {}
  assert second_store.set_calls == []

  asyncio.run(first.disable(first_name))
  enabled = asyncio.run(second.enable(second_name, app=fastapi.FastAPI()))
  assert enabled.enabled == (PEER_ID,)


def test_failed_startup_compensation_releases_runtime_claim(monkeypatch):
  state = InstalledExtension(name=NAME, version="1.0.0")
  failed, _, _ = make_host(state)

  def fail_load(self, extension_base):
    raise RuntimeError("load failed")

  monkeypatch.setattr(FakeModules, "load", fail_load)
  with pytest.raises(RuntimeError, match="load failed"):
    asyncio.run(failed.enable(NAME, app=fastapi.FastAPI()))
  assert ExtensionRuntimeClaim._owners == {}


def test_new_install_rejects_yanked_and_version_change_rejects_enabled_intent():
  missing = InstalledExtension(name=NAME, version="1.0.0", enabled=(PEER_ID,))
  host, _, _ = make_host(missing, release(version="2.0.0"))
  with pytest.raises(ExtensionStateConflictError):
    host.install(NAME, "2.0.0")

  fresh_host, _, _ = make_host(
    InstalledExtension(name="inkcre/another", version="1.0.0"),
    release(state="yanked"),
  )
  with pytest.raises(ExtensionCompatibilityError):
    fresh_host.install(NAME, "1.0.0")


def test_loaded_version_change_requires_restart_even_after_disable():
  state = InstalledExtension(name=NAME, version="1.0.0")
  host, _, _ = make_host(state, release(version="2.0.0"))
  host._loaded_versions[NAME] = "1.0.0"

  with pytest.raises(ExtensionRestartRequiredError):
    host.install(NAME, "2.0.0")


def test_disable_rpc_failure_restarts_exact_prior_runtime_and_preserves_intent():
  state = InstalledExtension(name=NAME, version="1.0.0", enabled=(PEER_ID,))
  host, store, _ = make_host(state)
  app = fastapi.FastAPI()
  asyncio.run(host.start_enabled(app))
  store.fail_set = True

  with pytest.raises(RuntimeError, match="RPC failed"):
    asyncio.run(host.disable(NAME))

  assert store.state is not None and store.state.enabled == (PEER_ID,)
  assert NAME in host.running
  assert FixtureExtension.runtime_active()


def test_disable_reports_both_rpc_and_restart_compensation_failures(monkeypatch):
  state = InstalledExtension(name=NAME, version="1.0.0", enabled=(PEER_ID,))
  host, store, _ = make_host(state)
  asyncio.run(host.start_enabled(fastapi.FastAPI()))
  store.fail_set = True

  async def fail_restart(*args, **kwargs):
    raise RuntimeError("restart failed")

  monkeypatch.setattr(host, "_start_acquired", fail_restart)
  with pytest.raises(ExceptionGroup) as caught:
    asyncio.run(host.disable(NAME))

  assert [str(error) for error in caught.value.exceptions] == [
    "RPC failed",
    "restart failed",
  ]
  assert store.state is not None and store.state.enabled == (PEER_ID,)


@pytest.mark.parametrize("phase", ["close", "unload"])
def test_partial_stop_failure_remains_tracked_and_never_mutates_enabled(phase: str):
  state = InstalledExtension(name=NAME, version="1.0.0", enabled=(PEER_ID,))
  host, store, _ = make_host(state)
  app = fastapi.FastAPI()
  asyncio.run(host.start_enabled(app))
  if phase == "close":
    FixtureExtension.fail_close = True
  else:
    FakeModules.fail_unload = True

  with pytest.raises(RuntimeError, match=f"{phase} failed"):
    asyncio.run(host.disable(NAME))

  assert NAME in host.running
  assert store.set_calls == []
  assert store.state is not None and store.state.enabled == (PEER_ID,)
  assert FixtureExtension.runtime_active() is (phase == "close")


def test_host_sdk_uses_npm_semver_ranges_and_prerelease_rules():
  descriptor = release()
  assert require_python_association(descriptor).host_sdk_version == "^0.1.0"
  assert require_python_association(
    descriptor.model_copy(update={"python": association(">=0.1.0 <0.2.0")})
  )
  with pytest.raises(ExtensionCompatibilityError):
    require_python_association(
      descriptor.model_copy(update={"python": association("^0.2.0")})
    )
  with pytest.raises(ExtensionCompatibilityError):
    require_python_association(
      descriptor.model_copy(update={"python": association(">=0.1.2-beta.1")})
    )


@pytest.mark.parametrize(
  "malicious",
  [
    "https://evil.test/simple/inkcre-extension-fixture/",
    "https://registry.test@evil.test/simple/inkcre-extension-fixture/",
    "/simple/inkcre-extension-fixture/?download=1",
    "/simple/inkcre-extension-fixture/#fragment",
    "/other/inkcre-extension-fixture/",
  ],
)
def test_simple_url_rejects_external_or_noncanonical_locations(malicious: str):
  value = association().model_copy(update={"simple_url": malicious})
  with pytest.raises(ExtensionCompatibilityError):
    simple_project_and_index_urls("https://registry.test", value)


def test_simple_url_resolves_only_the_registry_native_index():
  assert simple_project_and_index_urls("https://registry.test", association()) == (
    "https://registry.test/simple/inkcre-extension-fixture/",
    "https://registry.test/simple/",
  )
