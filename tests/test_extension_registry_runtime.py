"""Focused state-machine and exact-bundle tests for Registry Extensions."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import hashlib
from pathlib import Path
import sys
import threading
import typing
import uuid
import zipfile

import fastapi
from inkcre_extension_registry import (
  Condition,
  FileDescriptor,
  ReleaseRecord,
  TargetManifest,
)
from inkcre_extension_registry.contracts.models import TargetRecord
import pytest
import sqlmodel

from app.business.client import ClientManager
from app.business.extension import main as legacy_extension_module
from app.business.extension.main import ExtensionBase, ExtensionManager
from app.business.extension.registry import (
  REGISTRY_EXTENSION_MANAGER,
  AdmittedTarget,
  AdmittedTargetCatalog,
  RegistryBundleModules,
  RegistryExtensionManager,
  RegistryInstallationConflictError,
  RegistryInstallationNotFoundError,
  RegistryResolutionError,
  RegistryTargetAdmissionError,
)
from app.business.extension.runtime import (
  ExtensionPublicationSnapshot,
  ExtensionRuntimeClaim,
  ExtensionRuntimeClaimConflictError,
  ExtensionRuntimeRecord,
)
from app.business.info_base.resolver import ResolverManager
from app.business.source import SourceManager
from app.schemas.extension.registry import (
  ExtensionInstallationModel,
  ExtensionPeerBindingModel,
)
from app.schemas.extension.main import ExtensionModel
from app.routes.extension import (
  _raise_registry_http_error,
  update_registry_extension_config,
)
from scripts.build_extension_target import build_python_bundle


PEER_ID = uuid.UUID("10000000-0000-4000-8000-000000000001")
OTHER_PEER_ID = uuid.UUID("20000000-0000-4000-8000-000000000002")
SOURCE_TYPE = "extensions.fixture_ext.source.Source"
RESOLVER_TYPE = "extensions.fixture_ext.resolver"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class MemoryRegistryStore:
  def __init__(self) -> None:
    self.installations: dict[tuple[str, str], ExtensionInstallationModel] = {}
    self.bindings: dict[tuple[str, str, uuid.UUID], ExtensionPeerBindingModel] = {}
    self.events: list[str] = []
    self.before_delete_binding: Callable[[], None] | None = None
    self.create_binding_error: Exception | None = None

  def list_installations(self) -> tuple[ExtensionInstallationModel, ...]:
    return tuple(self.installations.values())

  def get_installation(
    self, namespace: str, name: str
  ) -> ExtensionInstallationModel | None:
    return self.installations.get((namespace, name))

  def put_installation(
    self, namespace: str, name: str, version: str
  ) -> ExtensionInstallationModel:
    key = (namespace, name)
    installation = self.installations.get(key)
    if installation is None:
      installation = ExtensionInstallationModel(
        namespace=namespace,
        name=name,
        version=version,
        config={},
        config_schema={},
      )
      self.installations[key] = installation
    elif installation.version != version:
      if any(
        binding.namespace == namespace and binding.name == name
        for binding in self.bindings.values()
      ):
        raise RegistryInstallationConflictError("bindings exist")
      installation.version = version
    return installation

  def delete_installation(self, namespace: str, name: str) -> None:
    key = (namespace, name)
    if key not in self.installations:
      raise RegistryInstallationNotFoundError("not installed")
    if any(
      binding.namespace == namespace and binding.name == name
      for binding in self.bindings.values()
    ):
      raise RegistryInstallationConflictError("bindings exist")
    del self.installations[key]

  def update_config(
    self, namespace: str, name: str, config: dict[str, typing.Any]
  ) -> ExtensionInstallationModel:
    installation = self.installations[(namespace, name)]
    installation.config = config
    return installation

  def update_config_schema(
    self, namespace: str, name: str, schema: dict[str, typing.Any]
  ) -> ExtensionInstallationModel:
    installation = self.installations[(namespace, name)]
    installation.config_schema = schema
    return installation

  def get_binding(
    self, namespace: str, name: str, peer_id: uuid.UUID
  ) -> ExtensionPeerBindingModel | None:
    return self.bindings.get((namespace, name, peer_id))

  def list_bindings_for_peer(
    self, peer_id: uuid.UUID
  ) -> tuple[ExtensionPeerBindingModel, ...]:
    return tuple(
      binding for binding in self.bindings.values() if binding.peer_id == peer_id
    )

  def create_binding(self, binding: ExtensionPeerBindingModel) -> ExtensionPeerBindingModel:
    if self.create_binding_error is not None:
      raise self.create_binding_error
    self.events.append("create-binding")
    self.bindings[(binding.namespace, binding.name, binding.peer_id)] = binding
    return binding

  def delete_binding(self, namespace: str, name: str, peer_id: uuid.UUID) -> None:
    if self.before_delete_binding is not None:
      self.before_delete_binding()
    self.events.append("delete-binding")
    self.bindings.pop((namespace, name, peer_id), None)


class FakeRegistryClient:
  def __init__(self, release: ReleaseRecord | Exception) -> None:
    self.release = release
    self.calls: list[tuple[str, str, str]] = []

  def get_release(self, namespace: str, name: str, version: str) -> ReleaseRecord:
    self.calls.append((namespace, name, version))
    if isinstance(self.release, Exception):
      raise self.release
    return self.release

  def close(self) -> None:
    pass


def _bundle_source() -> dict[str, str]:
  return {
    "extensions/__init__.py": "",
    "extensions/fixture_ext/__init__.py": """
import sqlmodel
from app.business.extension.main import ExtensionBase

class Config(sqlmodel.SQLModel):
  label: str = "ready"
  fail_close: bool = False

class Extension(ExtensionBase[Config], ext_id="fixture_ext", config_cls=Config):
  @classmethod
  def _register_apis(cls, router):
    router.get("/probe")(lambda: {"label": cls.config.label})

  @classmethod
  def _init_sources(cls):
    from app.business.source import SourceManager
    from .source import Source
    SourceManager.add_source_type(Source)

  @classmethod
  def _init_resolvers(cls):
    from app.business.info_base.resolver import ResolverManager
    from .resolver import FixtureResolver
    ResolverManager.register_resolver(FixtureResolver)

  @classmethod
  async def on_close(cls):
    if cls.config.fail_close:
      raise RuntimeError("fixture close failed")
    await super().on_close()
""",
    "extensions/fixture_ext/source.py": """
import sqlmodel
from app.business.source import SourceBase

class Config(sqlmodel.SQLModel):
  pass

class Source(SourceBase[Config], config_cls=Config):
  async def collect(self, job):
    pass

  async def _organize(self, block_id):
    pass
""",
    "extensions/fixture_ext/resolver.py": """
from app.business.info_base.resolver import Resolver

class FixtureResolver(Resolver[str, str], rso_type="extensions.fixture_ext.resolver"):
  async def get_text(self):
    return await self.get_raw_content()

  async def get_str_for_embedding(self):
    return await self.get_text()
""",
  }


def build_admitted_target(tmp_path: Path) -> tuple[AdmittedTarget, TargetRecord]:
  bundle_path = tmp_path / "bundle.zip"
  with zipfile.ZipFile(bundle_path, "w") as archive:
    for name, content in _bundle_source().items():
      archive.writestr(name, content)
  bundle = bundle_path.read_bytes()
  conditions = (
    Condition(key="inkcre.integration", operator="equals", value="python-bundle-v1"),
    Condition(key="inkcre.extension-api", operator="semver", value="^1.0.0"),
    Condition(key="python", operator="semver", value=">=3.12.0 <3.13.0"),
  )
  manifest = TargetManifest(
    artifact_format="python-bundle-v1",
    entrypoint="bundle.zip",
    conditions=conditions,
    files={
      "bundle.zip": FileDescriptor(
        sha256=hashlib.sha256(bundle).hexdigest(),
        size=len(bundle),
        media_type="application/zip",
      )
    },
  )
  manifest_path = tmp_path / "manifest.json"
  manifest_path.write_text(manifest.model_dump_json(), encoding="utf-8")
  admitted = AdmittedTarget(
    namespace="inkcre",
    name="fixture",
    version="0.1.0",
    target_key="python-core-v1",
    target_digest=manifest.digest,
    extension_id="fixture_ext",
    bundle_path=bundle_path,
    manifest_path=manifest_path,
  )
  target = TargetRecord(
    target_key=admitted.target_key,
    target_digest=admitted.target_digest,
    artifact_format="python-bundle-v1",
    entrypoint="bundle.zip",
    conditions=conditions,
  )
  return admitted, target


def release_for(target: TargetRecord, version: str = "0.1.0") -> ReleaseRecord:
  return ReleaseRecord(
    namespace="inkcre",
    name="fixture",
    version=version,
    state="published",
    targets=(target,),
  )


def build_manager(
  store: MemoryRegistryStore,
  admitted: AdmittedTarget,
  client: FakeRegistryClient,
) -> RegistryExtensionManager:
  return RegistryExtensionManager(
    store=store,
    catalog=AdmittedTargetCatalog([admitted]),
    registry_client_factory=lambda: typing.cast(typing.Any, client),
  )


@pytest.fixture(autouse=True)
def registry_runtime_isolation(monkeypatch):
  monkeypatch.setattr(ClientManager, "get_current_client_id", lambda: PEER_ID)
  monkeypatch.setattr(ExtensionRuntimeClaim, "_owners", {})
  ExtensionManager.RUNNING_EXTENSIONS.clear()
  ExtensionManager.RUNNING_CLAIMS.clear()
  yield
  SourceManager._SOURCE_CLASSES.pop(SOURCE_TYPE, None)
  ResolverManager.RESOLVER_CLS.pop(RESOLVER_TYPE, None)
  for module_name in tuple(sys.modules):
    if module_name == "extensions.fixture_ext" or module_name.startswith(
      "extensions.fixture_ext."
    ):
      sys.modules.pop(module_name, None)


def test_catalog_fails_closed_for_absent_invalid_and_tampered_bytes(tmp_path: Path):
  with pytest.raises(RegistryTargetAdmissionError, match="unavailable or invalid"):
    AdmittedTargetCatalog.load(tmp_path / "missing.json")

  invalid_path = tmp_path / "invalid.json"
  invalid_path.write_text('{"schema_version":1,"targets":{}}', encoding="utf-8")
  with pytest.raises(RegistryTargetAdmissionError, match="unsupported"):
    AdmittedTargetCatalog.load(invalid_path)

  admitted, _ = build_admitted_target(tmp_path)
  admitted.bundle_path.write_bytes(admitted.bundle_path.read_bytes() + b"tampered")
  with pytest.raises(RegistryTargetAdmissionError, match="bundle bytes"):
    AdmittedTargetCatalog([admitted]).require(
      admitted.namespace,
      admitted.name,
      admitted.version,
      admitted.target_key,
      admitted.target_digest,
    )


def test_registry_resolution_failures_map_to_bad_gateway():
  with pytest.raises(fastapi.HTTPException) as response:
    _raise_registry_http_error(RegistryResolutionError("upstream 404"))
  assert response.value.status_code == fastapi.status.HTTP_502_BAD_GATEWAY


def test_registry_config_validation_failure_maps_to_unprocessable_content(monkeypatch):
  class Config(sqlmodel.SQLModel):
    count: int

  def reject_config(*_args, **_kwargs):
    Config.model_validate({"count": "not-an-integer"})

  monkeypatch.setattr(REGISTRY_EXTENSION_MANAGER, "update_config", reject_config)

  with pytest.raises(fastapi.HTTPException) as response:
    update_registry_extension_config("inkcre", "fixture", {"count": "invalid"})

  assert response.value.status_code == fastapi.status.HTTP_422_UNPROCESSABLE_CONTENT
  detail = typing.cast(list[dict[str, typing.Any]], response.value.detail)
  assert detail[0]["type"] == "int_parsing"


def test_runtime_claim_is_atomic_and_release_is_idempotent():
  barrier = threading.Barrier(8)
  claims: list[ExtensionRuntimeClaim] = []
  conflicts: list[ExtensionRuntimeClaimConflictError] = []
  result_lock = threading.Lock()

  def compete() -> None:
    barrier.wait()
    try:
      claim = ExtensionRuntimeClaim.acquire("shared_runtime")
    except ExtensionRuntimeClaimConflictError as error:
      with result_lock:
        conflicts.append(error)
    else:
      with result_lock:
        claims.append(claim)

  threads = [threading.Thread(target=compete) for _ in range(barrier.parties)]
  for thread in threads:
    thread.start()
  for thread in threads:
    thread.join()

  assert len(claims) == 1
  assert len(conflicts) == barrier.parties - 1
  claims[0].release()
  claims[0].release()
  ExtensionRuntimeClaim.acquire("shared_runtime").release()


def test_publication_restore_is_idempotent():
  app = fastapi.FastAPI()
  snapshot = ExtensionPublicationSnapshot.capture(app)
  app.get("/temporary")(lambda: None)
  publication = snapshot.finish()

  publication.restore()
  publication.restore()

  assert "/temporary" not in app.openapi()["paths"]


def test_legacy_artifact_sync_only_creates_legacy_rows(monkeypatch):
  added: list[typing.Any] = []

  class Result:
    def first(self):
      return None

    def all(self):
      return list(added)

  class Session:
    def __enter__(self):
      return self

    def __exit__(self, *_args):
      pass

    def exec(self, _statement):
      return Result()

    def add(self, value):
      added.append(value)

    def commit(self):
      pass

  monkeypatch.setattr(legacy_extension_module, "SessionLocal", Session)

  ExtensionManager.sync()

  assert added
  assert all(isinstance(value, ExtensionModel) for value in added)
  assert not any(isinstance(value, ExtensionInstallationModel) for value in added)


def test_install_is_disabled_idempotent_and_rejects_version_change_with_binding(
  tmp_path: Path,
):
  admitted, target = build_admitted_target(tmp_path)
  client = FakeRegistryClient(release_for(target))
  store = MemoryRegistryStore()
  manager = build_manager(store, admitted, client)

  installed = manager.install("inkcre", "fixture", "0.1.0")
  assert installed.version == "0.1.0"
  assert store.bindings == {}
  assert manager.install("inkcre", "fixture", "0.1.0") is installed
  assert client.calls == [("inkcre", "fixture", "0.1.0")]

  store.create_binding(
    ExtensionPeerBindingModel(
      namespace="inkcre",
      name="fixture",
      version="0.1.0",
      peer_id=OTHER_PEER_ID,
      target_key=admitted.target_key,
      target_digest=admitted.target_digest,
    )
  )
  client.release = release_for(target, version="0.2.0")
  with pytest.raises(RegistryInstallationConflictError, match="bindings"):
    manager.install("inkcre", "fixture", "0.2.0")
  assert installed.version == "0.1.0"


def test_unknown_or_mismatched_target_and_registry_failure_do_not_import_or_bind(
  tmp_path: Path,
  monkeypatch,
):
  admitted, target = build_admitted_target(tmp_path)
  store = MemoryRegistryStore()
  store.put_installation("inkcre", "fixture", "0.1.0")
  client = FakeRegistryClient(release_for(target))
  manager = RegistryExtensionManager(
    store=store,
    catalog=AdmittedTargetCatalog([]),
    registry_client_factory=lambda: typing.cast(typing.Any, client),
  )
  monkeypatch.setattr(
    RegistryBundleModules,
    "load",
    lambda _self: (_ for _ in ()).throw(AssertionError("must not import")),
  )

  with pytest.raises(RegistryTargetAdmissionError, match="not admitted"):
    asyncio.run(manager.enable("inkcre", "fixture", app=fastapi.FastAPI()))
  assert store.bindings == {}

  mismatched = target.model_copy(update={"target_digest": f"sha256:{'f' * 64}"})
  client.release = release_for(mismatched)
  manager = build_manager(store, admitted, client)
  with pytest.raises(RegistryTargetAdmissionError, match="digest"):
    asyncio.run(manager.enable("inkcre", "fixture", app=fastapi.FastAPI()))
  assert store.bindings == {}

  client.release = RuntimeError("offline")
  with pytest.raises(RegistryResolutionError, match="could not resolve"):
    asyncio.run(manager.enable("inkcre", "fixture", app=fastapi.FastAPI()))
  assert store.bindings == {}


def test_enable_loads_exact_zip_then_disable_unpublishes_before_binding_delete(
  tmp_path: Path,
):
  admitted, target = build_admitted_target(tmp_path)
  client = FakeRegistryClient(release_for(target))
  store = MemoryRegistryStore()
  manager = build_manager(store, admitted, client)
  manager.install("inkcre", "fixture", "0.1.0")
  app = fastapi.FastAPI()
  app.openapi()

  binding = asyncio.run(manager.enable("inkcre", "fixture", app=app))

  assert binding.version == "0.1.0"
  assert store.events[-1] == "create-binding"
  assert "/fixture_ext/probe" in app.openapi()["paths"]
  assert SOURCE_TYPE in SourceManager._SOURCE_CLASSES
  assert RESOLVER_TYPE in ResolverManager.RESOLVER_CLS
  running = manager.running_extensions[("inkcre", "fixture")]
  running.modules.assert_admitted_origins()
  assert admitted.bundle_path.as_posix() in typing.cast(
    str, sys.modules["extensions.fixture_ext"].__file__
  )

  def assert_unpublished() -> None:
    assert "/fixture_ext/probe" not in app.openapi()["paths"]
    assert SOURCE_TYPE not in SourceManager._SOURCE_CLASSES
    assert RESOLVER_TYPE not in ResolverManager.RESOLVER_CLS
    assert "extensions.fixture_ext" not in sys.modules

  store.before_delete_binding = assert_unpublished
  asyncio.run(manager.disable("inkcre", "fixture"))

  assert store.get_binding("inkcre", "fixture", PEER_ID) is None
  assert manager.running_extensions == {}

  # A second enable imports the exact zip afresh and republishes every surface.
  asyncio.run(manager.enable("inkcre", "fixture", app=app))
  assert "/fixture_ext/probe" in app.openapi()["paths"]
  assert SOURCE_TYPE in SourceManager._SOURCE_CLASSES
  assert RESOLVER_TYPE in ResolverManager.RESOLVER_CLS
  store.before_delete_binding = None
  asyncio.run(manager.disable("inkcre", "fixture"))


def test_teardown_failure_keeps_binding_and_retry_can_complete(tmp_path: Path, monkeypatch):
  admitted, target = build_admitted_target(tmp_path)
  store = MemoryRegistryStore()
  manager = build_manager(store, admitted, FakeRegistryClient(release_for(target)))
  manager.install("inkcre", "fixture", "0.1.0")
  app = fastapi.FastAPI()
  asyncio.run(manager.enable("inkcre", "fixture", app=app))
  running = manager.running_extensions[("inkcre", "fixture")]

  async def fail_close(_cls) -> None:
    raise RuntimeError("close failed")

  with monkeypatch.context() as scoped:
    scoped.setattr(running.extension_class, "on_close", classmethod(fail_close))
    with pytest.raises(RuntimeError, match="close failed"):
      asyncio.run(manager.disable("inkcre", "fixture"))

  assert store.get_binding("inkcre", "fixture", PEER_ID) is not None
  assert "/fixture_ext/probe" in app.openapi()["paths"]
  assert ("inkcre", "fixture") in manager.running_extensions

  asyncio.run(manager.disable("inkcre", "fixture"))
  assert store.get_binding("inkcre", "fixture", PEER_ID) is None


def test_legacy_start_cannot_replace_same_id_registry_runtime(tmp_path: Path):
  admitted, target = build_admitted_target(tmp_path)
  store = MemoryRegistryStore()
  manager = build_manager(store, admitted, FakeRegistryClient(release_for(target)))
  manager.install("inkcre", "fixture", "0.1.0")
  app = fastapi.FastAPI()
  asyncio.run(manager.enable("inkcre", "fixture", app=app))

  with pytest.raises(RuntimeError, match="already owns the canonical module"):
    ExtensionManager.start(
      extension=ExtensionModel(
        id="fixture_ext",
        version="0.1.0",
        enabled=[],
        config={},
      ),
      app=app,
    )

  assert "fixture_ext" not in ExtensionManager.RUNNING_EXTENSIONS
  assert ("inkcre", "fixture") in manager.running_extensions
  manager.running_extensions[("inkcre", "fixture")].modules.assert_admitted_origins()
  assert "/fixture_ext/probe" in app.openapi()["paths"]
  asyncio.run(manager.disable("inkcre", "fixture"))


def test_bootstrap_uses_persisted_exact_binding_without_registry(tmp_path: Path):
  admitted, target = build_admitted_target(tmp_path)
  store = MemoryRegistryStore()
  first_client = FakeRegistryClient(release_for(target))
  first = build_manager(store, admitted, first_client)
  first.install("inkcre", "fixture", "0.1.0")
  app = fastapi.FastAPI()
  binding = asyncio.run(first.enable("inkcre", "fixture", app=app))
  asyncio.run(first.close_running())
  assert store.get_binding("inkcre", "fixture", PEER_ID) is binding

  offline = FakeRegistryClient(RuntimeError("Registry must not be used"))
  restarted = build_manager(store, admitted, offline)
  asyncio.run(restarted.start_enabled(app))
  assert offline.calls == []
  assert restarted.running_extensions[("inkcre", "fixture")].binding.version == "0.1.0"
  asyncio.run(restarted.disable("inkcre", "fixture"))


def test_uninstall_requires_zero_bindings(tmp_path: Path):
  admitted, target = build_admitted_target(tmp_path)
  store = MemoryRegistryStore()
  manager = build_manager(store, admitted, FakeRegistryClient(release_for(target)))
  manager.install("inkcre", "fixture", "0.1.0")
  store.create_binding(
    ExtensionPeerBindingModel(
      namespace="inkcre",
      name="fixture",
      version="0.1.0",
      peer_id=OTHER_PEER_ID,
      target_key=admitted.target_key,
      target_digest=admitted.target_digest,
    )
  )

  with pytest.raises(RegistryInstallationConflictError, match="bindings"):
    manager.uninstall("inkcre", "fixture")
  store.delete_binding("inkcre", "fixture", OTHER_PEER_ID)
  manager.uninstall("inkcre", "fixture")
  assert store.installations == {}


def test_binding_write_failure_forcibly_removes_unbound_runtime(tmp_path: Path):
  admitted, target = build_admitted_target(tmp_path)
  store = MemoryRegistryStore()
  manager = build_manager(store, admitted, FakeRegistryClient(release_for(target)))
  manager.install("inkcre", "fixture", "0.1.0")
  store.update_config("inkcre", "fixture", {"fail_close": True})
  store.create_binding_error = RuntimeError("binding write failed")
  app = fastapi.FastAPI()

  with pytest.raises(ExceptionGroup) as failure:
    asyncio.run(manager.enable("inkcre", "fixture", app=app))

  assert "binding write failed" in str(failure.value.exceptions[0])
  assert "fixture close failed" in str(failure.value.exceptions[1])
  assert store.bindings == {}
  assert manager.running_extensions == {}
  assert "/fixture_ext/probe" not in app.openapi()["paths"]
  assert SOURCE_TYPE not in SourceManager._SOURCE_CLASSES
  assert RESOLVER_TYPE not in ResolverManager.RESOLVER_CLS
  assert "extensions.fixture_ext" not in sys.modules


def test_uninstall_rejects_an_active_runtime_even_without_a_binding(tmp_path: Path):
  admitted, target = build_admitted_target(tmp_path)
  store = MemoryRegistryStore()
  manager = build_manager(store, admitted, FakeRegistryClient(release_for(target)))
  manager.install("inkcre", "fixture", "0.1.0")
  app = fastapi.FastAPI()
  asyncio.run(manager.enable("inkcre", "fixture", app=app))
  store.bindings.clear()

  with pytest.raises(RegistryInstallationConflictError, match="runtime is active"):
    manager.uninstall("inkcre", "fixture")

  asyncio.run(manager.close_running())
  manager.uninstall("inkcre", "fixture")


def test_twitter_zip_keeps_canonical_source_and_resolver_identity(tmp_path: Path):
  bundle_path = tmp_path / "bundle.zip"
  build_python_bundle(PROJECT_ROOT, "twitter", bundle_path)
  bundle = bundle_path.read_bytes()
  conditions = (
    Condition(key="inkcre.integration", operator="equals", value="python-bundle-v1"),
    Condition(key="inkcre.extension-api", operator="semver", value="^1.0.0"),
    Condition(key="python", operator="semver", value=">=3.12.0 <3.13.0"),
  )
  manifest = TargetManifest(
    artifact_format="python-bundle-v1",
    entrypoint="bundle.zip",
    conditions=conditions,
    files={
      "bundle.zip": FileDescriptor(
        sha256=hashlib.sha256(bundle).hexdigest(),
        size=len(bundle),
        media_type="application/zip",
      )
    },
  )
  manifest_path = tmp_path / "manifest.json"
  manifest_path.write_text(manifest.model_dump_json(), encoding="utf-8")
  admitted = AdmittedTarget(
    namespace="inkcre",
    name="twitter",
    version="0.1.0",
    target_key="python-core-v1",
    target_digest=manifest.digest,
    extension_id="twitter",
    bundle_path=bundle_path,
    manifest_path=manifest_path,
  )
  target = TargetRecord(
    target_key=admitted.target_key,
    target_digest=admitted.target_digest,
    artifact_format="python-bundle-v1",
    entrypoint="bundle.zip",
    conditions=conditions,
  )
  release = ReleaseRecord(
    namespace="inkcre",
    name="twitter",
    version="0.1.0",
    state="published",
    targets=(target,),
  )
  store = MemoryRegistryStore()
  manager = build_manager(store, admitted, FakeRegistryClient(release))
  manager.install("inkcre", "twitter", "0.1.0")
  app = fastapi.FastAPI()

  asyncio.run(manager.enable("inkcre", "twitter", app=app))

  assert "extensions.twitter.bookmark.Source" in SourceManager._SOURCE_CLASSES
  assert "extensions.twitter.tweet" in ResolverManager.RESOLVER_CLS
  manager.running_extensions[("inkcre", "twitter")].modules.assert_admitted_origins()
  twitter_api_module = sys.modules["extensions.twitter.api"]
  assert twitter_api_module.TwitterAPI.SINGLETON is not None
  asyncio.run(manager.disable("inkcre", "twitter"))

  assert "extensions.twitter.bookmark.Source" not in SourceManager._SOURCE_CLASSES
  assert "extensions.twitter.tweet" not in ResolverManager.RESOLVER_CLS
  assert twitter_api_module.TwitterAPI.SINGLETON is None

  asyncio.run(manager.enable("inkcre", "twitter", app=app))
  assert "extensions.twitter.bookmark.Source" in SourceManager._SOURCE_CLASSES
  assert "extensions.twitter.tweet" in ResolverManager.RESOLVER_CLS
  asyncio.run(manager.disable("inkcre", "twitter"))


def test_legacy_running_map_closes_by_extension_id_and_removes_routes():
  app = fastapi.FastAPI()
  events: list[str] = []

  class Config(sqlmodel.SQLModel):
    pass

  class FixtureExtension(ExtensionBase[Config], ext_id="legacy_fixture", config_cls=Config):
    @classmethod
    def _register_apis(cls, router):
      router.get("/probe")(lambda: None)

    @classmethod
    async def on_close(cls):
      events.append("close")
      await super().on_close()

  record = ExtensionRuntimeRecord(
    extension_id="legacy_fixture",
    config={},
    persist_config=lambda _config: None,
    persist_config_schema=lambda _schema: None,
  )
  FixtureExtension.on_start(app, record)
  ExtensionManager.RUNNING_EXTENSIONS["legacy_fixture"] = FixtureExtension

  asyncio.run(ExtensionManager.close("legacy_fixture"))

  assert events == ["close"]
  assert "legacy_fixture" not in ExtensionManager.RUNNING_EXTENSIONS
  assert "/legacy_fixture/probe" not in app.openapi()["paths"]
