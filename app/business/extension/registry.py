"""Registry-backed Extension installation, admission, and peer lifecycle."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterable
import contextlib
from dataclasses import dataclass
import hashlib
import importlib
import json
from pathlib import Path, PurePosixPath
import platform
import re
import sys
import typing
import uuid
import zipfile
import zipimport

import fastapi
from inkcre_extension_registry import (
  ReleaseRecord,
  TargetManifest,
  TargetRecord,
  select_compatible_target,
  target_matches,
)
from inkcre_extension_registry.client import RegistryClient
from inkcre_extension_registry.contracts.models import (
  DIGEST_PATTERN,
  validate_segment,
  validate_target_key,
  validate_version,
)
import sqlmodel

from app.business.client import ClientManager
from app.engine import SessionLocal
from app.schemas.extension.registry import (
  ExtensionInstallationModel,
  ExtensionPeerBindingModel,
)
from app.settings import settings

from .main import ExtensionBase, ExtensionManager
from .runtime import (
  ExtensionPublicationSnapshot,
  ExtensionRuntimeClaim,
  ExtensionRuntimeClaimConflictError,
  ExtensionRuntimeRecord,
)


PYTHON_ARTIFACT_FORMAT = "python-bundle-v1"
EXTENSION_API_VERSION = "1.0.0"
_EXTENSION_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class RegistryExtensionError(RuntimeError):
  """Base error for the Registry-backed deployment state path."""


class RegistryInstallationNotFoundError(RegistryExtensionError):
  pass


class RegistryInstallationConflictError(RegistryExtensionError):
  pass


class RegistryResolutionError(RegistryExtensionError):
  pass


class RegistryTargetNotCompatibleError(RegistryExtensionError):
  pass


class RegistryTargetAdmissionError(RegistryExtensionError):
  pass


class RegistryRuntimeConflictError(RegistryExtensionError):
  pass


@dataclass(frozen=True)
class AdmittedTarget:
  """One build-admitted coordinate mapped to immutable local bytes."""

  namespace: str
  name: str
  version: str
  target_key: str
  target_digest: str
  extension_id: str
  bundle_path: Path
  manifest_path: Path

  @property
  def slot(self) -> tuple[str, str, str, str]:
    return (self.namespace, self.name, self.version, self.target_key)

  def verify_artifact(self) -> TargetManifest:
    """Prove the catalog digest names the manifest and exact bundle bytes."""
    try:
      manifest = TargetManifest.model_validate_json(
        self.manifest_path.read_text(encoding="utf-8")
      )
    except Exception as error:
      raise RegistryTargetAdmissionError(
        f"Admitted target manifest is unavailable or invalid: {self.manifest_path}"
      ) from error

    if manifest.digest != self.target_digest:
      raise RegistryTargetAdmissionError(
        "Admitted target manifest digest does not match the persisted target"
      )
    if manifest.artifact_format != PYTHON_ARTIFACT_FORMAT:
      raise RegistryTargetAdmissionError("Admitted target is not a Python bundle")

    descriptor = manifest.files.get(manifest.entrypoint)
    if descriptor is None:
      raise RegistryTargetAdmissionError("Admitted target entrypoint is not declared")
    if not self.bundle_path.is_file():
      raise RegistryTargetAdmissionError(
        f"Admitted target bundle is unavailable: {self.bundle_path}"
      )

    size = 0
    digest = hashlib.sha256()
    try:
      with self.bundle_path.open("rb") as bundle:
        for chunk in iter(lambda: bundle.read(1024 * 1024), b""):
          size += len(chunk)
          digest.update(chunk)
    except OSError as error:
      raise RegistryTargetAdmissionError(
        f"Cannot read admitted target bundle: {self.bundle_path}"
      ) from error
    if size != descriptor.size or digest.hexdigest() != descriptor.sha256:
      raise RegistryTargetAdmissionError(
        "Admitted target bundle bytes do not match its target manifest"
      )

    try:
      with zipfile.ZipFile(self.bundle_path) as archive:
        members = archive.namelist()
    except (OSError, zipfile.BadZipFile) as error:
      raise RegistryTargetAdmissionError(
        "Admitted Python bundle is not a valid zip"
      ) from error
    if len(members) != len(set(members)):
      raise RegistryTargetAdmissionError("Admitted Python bundle has duplicate members")
    for member in members:
      path = PurePosixPath(member)
      if (
        not member
        or "\\" in member
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
      ):
        raise RegistryTargetAdmissionError("Admitted Python bundle has an unsafe member")
    entrypoint = f"extensions/{self.extension_id}/__init__.py"
    if entrypoint not in members:
      raise RegistryTargetAdmissionError(
        f"Admitted Python bundle does not contain {entrypoint}"
      )
    return manifest


class AdmittedTargetCatalog:
  """Fail-closed loader for the catalog embedded by the application build."""

  def __init__(self, targets: Iterable[AdmittedTarget]) -> None:
    by_slot: dict[tuple[str, str, str, str], AdmittedTarget] = {}
    for target in targets:
      self._validate_target(target)
      existing = by_slot.get(target.slot)
      if existing is not None:
        raise RegistryTargetAdmissionError(
          "Admitted target catalog contains a duplicate target slot"
        )
      by_slot[target.slot] = target
    self._by_slot = by_slot

  @staticmethod
  def _validate_target(target: AdmittedTarget) -> None:
    try:
      validate_segment(target.namespace)
      validate_segment(target.name)
      validate_version(target.version)
      validate_target_key(target.target_key)
    except ValueError as error:
      raise RegistryTargetAdmissionError("Admitted target identity is invalid") from error
    if not DIGEST_PATTERN.fullmatch(target.target_digest):
      raise RegistryTargetAdmissionError("Admitted target digest is invalid")
    if not _EXTENSION_ID_PATTERN.fullmatch(target.extension_id):
      raise RegistryTargetAdmissionError("Admitted target extension_id is unsafe")

  @classmethod
  def load(cls, path: str | Path) -> AdmittedTargetCatalog:
    catalog_path = Path(path)
    try:
      value = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
      raise RegistryTargetAdmissionError(
        f"Admitted target catalog is unavailable or invalid: {catalog_path}"
      ) from error
    if not isinstance(value, dict) or set(value) != {"schema_version", "targets"}:
      raise RegistryTargetAdmissionError("Admitted target catalog shape is invalid")
    if value["schema_version"] != 1 or not isinstance(value["targets"], list):
      raise RegistryTargetAdmissionError("Admitted target catalog version is unsupported")

    expected_keys = {
      "namespace",
      "name",
      "version",
      "target_key",
      "target_digest",
      "extension_id",
      "bundle_path",
      "manifest_path",
    }
    targets: list[AdmittedTarget] = []
    for raw_target in value["targets"]:
      if not isinstance(raw_target, dict) or set(raw_target) != expected_keys:
        raise RegistryTargetAdmissionError("Admitted target catalog entry is invalid")
      if not all(isinstance(raw_target[key], str) for key in expected_keys):
        raise RegistryTargetAdmissionError("Admitted target catalog values must be strings")

      def artifact_path(key: str) -> Path:
        candidate = Path(raw_target[key])
        if not candidate.is_absolute():
          candidate = catalog_path.parent / candidate
        return candidate.resolve()

      targets.append(
        AdmittedTarget(
          namespace=raw_target["namespace"],
          name=raw_target["name"],
          version=raw_target["version"],
          target_key=raw_target["target_key"],
          target_digest=raw_target["target_digest"],
          extension_id=raw_target["extension_id"],
          bundle_path=artifact_path("bundle_path"),
          manifest_path=artifact_path("manifest_path"),
        )
      )
    return cls(targets)

  def require(
    self,
    namespace: str,
    name: str,
    version: str,
    target_key: str,
    target_digest: str,
  ) -> AdmittedTarget:
    target = self._by_slot.get((namespace, name, version, target_key))
    if target is None:
      raise RegistryTargetAdmissionError("Registry target is not admitted by this build")
    if target.target_digest != target_digest:
      raise RegistryTargetAdmissionError(
        "Registry target digest does not match the build-admitted target"
      )
    target.verify_artifact()
    return target


class RegistryBundleModules:
  """Own canonical Extension modules loaded from one exact admitted zip."""

  def __init__(self, target: AdmittedTarget) -> None:
    self.target = target
    self.package_name = f"extensions.{target.extension_id}"
    self.bundle_path = target.bundle_path.resolve()
    self.bundle_extensions_path = f"{self.bundle_path.as_posix()}/extensions"
    self._previous_modules: dict[str, typing.Any] = {}
    self._parent: typing.Any = None
    self._path_added = False
    self._owns_modules = False
    self._active = False

  def _module_names(self) -> tuple[str, ...]:
    prefix = f"{self.package_name}."
    return tuple(
      name for name in sys.modules if name == self.package_name or name.startswith(prefix)
    )

  def _origin_is_admitted(self, module: typing.Any) -> bool:
    spec = getattr(module, "__spec__", None)
    if spec is None or not isinstance(getattr(spec, "loader", None), zipimport.zipimporter):
      return False
    origins = {
      origin
      for origin in (getattr(module, "__file__", None), getattr(spec, "origin", None))
      if isinstance(origin, str)
    }
    prefix = f"{self.bundle_path.as_posix()}/"
    return bool(origins) and all(origin.startswith(prefix) for origin in origins)

  def assert_admitted_origins(self) -> None:
    names = self._module_names()
    if self.package_name not in names:
      raise RegistryTargetAdmissionError("Admitted Extension package was not loaded")
    invalid = [name for name in names if not self._origin_is_admitted(sys.modules[name])]
    if invalid:
      raise RegistryTargetAdmissionError(
        "Registry Extension module did not originate from the admitted bundle: "
        + ", ".join(sorted(invalid))
      )

  def load(self) -> type[ExtensionBase]:
    if self._active:
      raise RegistryRuntimeConflictError("Admitted bundle module session is already active")
    self.target.verify_artifact()
    parent = importlib.import_module("extensions")
    parent_path = getattr(parent, "__path__", None)
    if parent_path is None:
      raise RegistryTargetAdmissionError("Canonical extensions package has no package path")
    self._parent = parent
    current_paths = [str(path) for path in parent_path]
    self._path_added = self.bundle_extensions_path not in current_paths
    if self._path_added:
      parent.__path__ = [self.bundle_extensions_path, *current_paths]

    self._previous_modules = {name: sys.modules[name] for name in self._module_names()}
    for name in self._previous_modules:
      sys.modules.pop(name, None)
    self._owns_modules = True
    importlib.invalidate_caches()
    try:
      module = importlib.import_module(self.package_name)
      self._active = True
      self.assert_admitted_origins()
      extension_class = getattr(module, "Extension", None)
      if not isinstance(extension_class, type) or not issubclass(
        extension_class, ExtensionBase
      ):
        raise RegistryTargetAdmissionError(
          "Admitted bundle entrypoint does not expose an Extension class"
        )
      if extension_class.__extid__ != self.target.extension_id:
        raise RegistryTargetAdmissionError(
          "Admitted bundle Extension identity does not match the local catalog"
        )
      return extension_class
    except Exception:
      self.abort()
      raise

  def _remove_bundle_path(self) -> None:
    if not self._path_added or self._parent is None:
      return
    self._parent.__path__ = [
      str(path)
      for path in self._parent.__path__
      if str(path) != self.bundle_extensions_path
    ]

  def abort(self) -> None:
    if self._owns_modules:
      for name in self._module_names():
        sys.modules.pop(name, None)
      sys.modules.update(self._previous_modules)
    self._remove_bundle_path()
    importlib.invalidate_caches()
    self._owns_modules = False
    self._active = False

  def unload(self) -> None:
    if not self._active:
      return
    self.assert_admitted_origins()
    for name in self._module_names():
      sys.modules.pop(name, None)
    sys.modules.update(self._previous_modules)
    self._remove_bundle_path()
    importlib.invalidate_caches()
    self._owns_modules = False
    self._active = False


class RegistryExtensionStore(typing.Protocol):
  def list_installations(self) -> tuple[ExtensionInstallationModel, ...]: ...

  def get_installation(
    self, namespace: str, name: str
  ) -> ExtensionInstallationModel | None: ...

  def put_installation(
    self, namespace: str, name: str, version: str
  ) -> ExtensionInstallationModel: ...

  def delete_installation(self, namespace: str, name: str) -> None: ...

  def update_config(
    self, namespace: str, name: str, config: dict[str, typing.Any]
  ) -> ExtensionInstallationModel: ...

  def update_config_schema(
    self, namespace: str, name: str, schema: dict[str, typing.Any]
  ) -> ExtensionInstallationModel: ...

  def get_binding(
    self, namespace: str, name: str, peer_id: uuid.UUID
  ) -> ExtensionPeerBindingModel | None: ...

  def list_bindings_for_peer(
    self, peer_id: uuid.UUID
  ) -> tuple[ExtensionPeerBindingModel, ...]: ...

  def create_binding(
    self, binding: ExtensionPeerBindingModel
  ) -> ExtensionPeerBindingModel: ...

  def delete_binding(self, namespace: str, name: str, peer_id: uuid.UUID) -> None: ...


class SQLRegistryExtensionStore:
  """Small transactional persistence adapter over the Stage A SQLModels."""

  def __init__(
    self, session_factory: Callable[[], sqlmodel.Session] = SessionLocal
  ) -> None:
    self._session_factory = session_factory

  def list_installations(self) -> tuple[ExtensionInstallationModel, ...]:
    with self._session_factory() as db:
      return tuple(db.exec(sqlmodel.select(ExtensionInstallationModel)).all())

  def get_installation(
    self, namespace: str, name: str
  ) -> ExtensionInstallationModel | None:
    with self._session_factory() as db:
      return db.exec(
        sqlmodel.select(ExtensionInstallationModel).where(
          ExtensionInstallationModel.namespace == namespace,
          ExtensionInstallationModel.name == name,
        )
      ).one_or_none()

  def put_installation(
    self, namespace: str, name: str, version: str
  ) -> ExtensionInstallationModel:
    with self._session_factory() as db:
      installation = db.exec(
        sqlmodel.select(ExtensionInstallationModel)
        .where(
          ExtensionInstallationModel.namespace == namespace,
          ExtensionInstallationModel.name == name,
        )
        .with_for_update()
      ).one_or_none()
      if installation is None:
        installation = ExtensionInstallationModel(
          namespace=namespace,
          name=name,
          version=version,
          config={},
          config_schema={},
        )
        db.add(installation)
      elif installation.version != version:
        binding = db.exec(
          sqlmodel.select(ExtensionPeerBindingModel).where(
            ExtensionPeerBindingModel.namespace == namespace,
            ExtensionPeerBindingModel.name == name,
          )
        ).first()
        if binding is not None:
          raise RegistryInstallationConflictError(
            f"Cannot change {namespace}/{name} version while peer bindings exist"
          )
        installation.version = version
        db.add(installation)
      db.commit()
      db.refresh(installation)
      return installation

  def delete_installation(self, namespace: str, name: str) -> None:
    with self._session_factory() as db:
      installation = db.exec(
        sqlmodel.select(ExtensionInstallationModel)
        .where(
          ExtensionInstallationModel.namespace == namespace,
          ExtensionInstallationModel.name == name,
        )
        .with_for_update()
      ).one_or_none()
      if installation is None:
        raise RegistryInstallationNotFoundError(f"{namespace}/{name} is not installed")
      binding = db.exec(
        sqlmodel.select(ExtensionPeerBindingModel).where(
          ExtensionPeerBindingModel.namespace == namespace,
          ExtensionPeerBindingModel.name == name,
        )
      ).first()
      if binding is not None:
        raise RegistryInstallationConflictError(
          f"Cannot uninstall {namespace}/{name} while peer bindings exist"
        )
      db.delete(installation)
      db.commit()

  def _update_installation(
    self,
    namespace: str,
    name: str,
    field: str,
    value: dict[str, typing.Any],
  ) -> ExtensionInstallationModel:
    with self._session_factory() as db:
      installation = db.exec(
        sqlmodel.select(ExtensionInstallationModel).where(
          ExtensionInstallationModel.namespace == namespace,
          ExtensionInstallationModel.name == name,
        )
      ).one_or_none()
      if installation is None:
        raise RegistryInstallationNotFoundError(f"{namespace}/{name} is not installed")
      setattr(installation, field, value)
      db.add(installation)
      db.commit()
      db.refresh(installation)
      return installation

  def update_config(
    self, namespace: str, name: str, config: dict[str, typing.Any]
  ) -> ExtensionInstallationModel:
    return self._update_installation(namespace, name, "config", config)

  def update_config_schema(
    self, namespace: str, name: str, schema: dict[str, typing.Any]
  ) -> ExtensionInstallationModel:
    return self._update_installation(namespace, name, "config_schema", schema)

  def get_binding(
    self, namespace: str, name: str, peer_id: uuid.UUID
  ) -> ExtensionPeerBindingModel | None:
    with self._session_factory() as db:
      return db.exec(
        sqlmodel.select(ExtensionPeerBindingModel).where(
          ExtensionPeerBindingModel.namespace == namespace,
          ExtensionPeerBindingModel.name == name,
          ExtensionPeerBindingModel.peer_id == peer_id,
        )
      ).one_or_none()

  def list_bindings_for_peer(
    self, peer_id: uuid.UUID
  ) -> tuple[ExtensionPeerBindingModel, ...]:
    with self._session_factory() as db:
      return tuple(
        db.exec(
          sqlmodel.select(ExtensionPeerBindingModel).where(
            ExtensionPeerBindingModel.peer_id == peer_id
          )
        ).all()
      )

  def create_binding(self, binding: ExtensionPeerBindingModel) -> ExtensionPeerBindingModel:
    with self._session_factory() as db:
      db.add(binding)
      db.commit()
      db.refresh(binding)
      return binding

  def delete_binding(self, namespace: str, name: str, peer_id: uuid.UUID) -> None:
    with self._session_factory() as db:
      binding = db.exec(
        sqlmodel.select(ExtensionPeerBindingModel).where(
          ExtensionPeerBindingModel.namespace == namespace,
          ExtensionPeerBindingModel.name == name,
          ExtensionPeerBindingModel.peer_id == peer_id,
        )
      ).one_or_none()
      if binding is not None:
        db.delete(binding)
        db.commit()


@dataclass
class RunningRegistryExtension:
  binding: ExtensionPeerBindingModel
  target: AdmittedTarget
  extension_class: type[ExtensionBase]
  modules: RegistryBundleModules
  runtime_claim: ExtensionRuntimeClaim


class RegistryExtensionManager:
  """Independent namespaced installation and current-peer runtime manager."""

  def __init__(
    self,
    *,
    store: RegistryExtensionStore | None = None,
    catalog: AdmittedTargetCatalog | None = None,
    registry_client_factory: Callable[[], RegistryClient] | None = None,
  ) -> None:
    self.store = store or SQLRegistryExtensionStore()
    self._catalog = catalog
    self._registry_client_factory = registry_client_factory or self._default_registry_client
    self.running_extensions: dict[tuple[str, str], RunningRegistryExtension] = {}
    self.fastapi_app: fastapi.FastAPI | None = None
    self._runtime_lock = asyncio.Lock()

  @staticmethod
  def _default_registry_client() -> RegistryClient:
    return RegistryClient(
      settings.extension_registry_url,
      timeout=settings.extension_registry_timeout_seconds,
    )

  def _admitted_catalog(self) -> AdmittedTargetCatalog:
    if self._catalog is not None:
      return self._catalog
    return AdmittedTargetCatalog.load(settings.extension_target_catalog_path)

  @staticmethod
  def platform_profile() -> dict[str, str]:
    return {
      "inkcre.integration": PYTHON_ARTIFACT_FORMAT,
      "inkcre.extension-api": EXTENSION_API_VERSION,
      "python": platform.python_version(),
    }

  def _resolve_release(self, namespace: str, name: str, version: str) -> ReleaseRecord:
    try:
      client = self._registry_client_factory()
      try:
        release = client.get_release(namespace, name, version)
      finally:
        with contextlib.suppress(Exception):
          client.close()
    except Exception as error:
      raise RegistryResolutionError(
        f"Registry could not resolve {namespace}/{name}@{version}"
      ) from error
    if (release.namespace, release.name, release.version) != (namespace, name, version):
      raise RegistryResolutionError("Registry returned a different release identity")
    if release.state != "published":
      raise RegistryResolutionError("Registry release is not published")
    return release

  @staticmethod
  def _validate_coordinate(namespace: str, name: str, version: str | None = None) -> None:
    try:
      validate_segment(namespace)
      validate_segment(name)
      if version is not None:
        validate_version(version)
    except ValueError as error:
      raise RegistryInstallationConflictError(
        "Registry coordinate is not canonical"
      ) from error

  def list_installations(self) -> tuple[ExtensionInstallationModel, ...]:
    return self.store.list_installations()

  def get_installation(self, namespace: str, name: str) -> ExtensionInstallationModel:
    self._validate_coordinate(namespace, name)
    installation = self.store.get_installation(namespace, name)
    if installation is None:
      raise RegistryInstallationNotFoundError(f"{namespace}/{name} is not installed")
    return installation

  def install(self, namespace: str, name: str, version: str) -> ExtensionInstallationModel:
    self._validate_coordinate(namespace, name, version)
    existing = self.store.get_installation(namespace, name)
    if existing is not None and existing.version == version:
      return existing
    self._resolve_release(namespace, name, version)
    return self.store.put_installation(namespace, name, version)

  def uninstall(self, namespace: str, name: str) -> None:
    self._validate_coordinate(namespace, name)
    if (namespace, name) in self.running_extensions:
      raise RegistryInstallationConflictError(
        f"Cannot uninstall {namespace}/{name} while its runtime is active"
      )
    self.store.delete_installation(namespace, name)

  def update_config(
    self,
    namespace: str,
    name: str,
    config: dict[str, typing.Any],
  ) -> ExtensionInstallationModel:
    installation = self.get_installation(namespace, name)
    running = self.running_extensions.get((namespace, name))
    if running is not None:
      config_class = typing.cast(
        type[sqlmodel.SQLModel],
        getattr(running.extension_class, "__configcls__"),
      )
      validated = config_class(**config)
      installation = self.store.update_config(namespace, name, validated.model_dump())
      running.extension_class.update_config(validated)
      return installation
    return self.store.update_config(namespace, name, config)

  @staticmethod
  def _require_binding_version(
    installation: ExtensionInstallationModel,
    binding: ExtensionPeerBindingModel,
  ) -> None:
    if binding.version != installation.version:
      raise RegistryInstallationConflictError(
        "Persisted peer binding version differs from the shared installation"
      )

  def _select_new_target(
    self,
    release: ReleaseRecord,
  ) -> TargetRecord:
    target = select_compatible_target(release.targets, self.platform_profile())
    if target is None or target.artifact_format != PYTHON_ARTIFACT_FORMAT:
      raise RegistryTargetNotCompatibleError(
        f"No compatible Python target exists for {release.namespace}/{release.name}"
      )
    return target

  @staticmethod
  def _require_registry_projection(
    selected: TargetRecord,
    admitted: AdmittedTarget,
  ) -> None:
    manifest = admitted.verify_artifact()
    selected_conditions = sorted(
      (condition.key, condition.operator, condition.value)
      for condition in selected.conditions
    )
    manifest_conditions = sorted(
      (condition.key, condition.operator, condition.value)
      for condition in manifest.conditions
    )
    if (
      selected.artifact_format != manifest.artifact_format
      or selected.entrypoint != manifest.entrypoint
      or selected_conditions != manifest_conditions
    ):
      raise RegistryTargetAdmissionError(
        "Registry target projection differs from its admitted manifest"
      )

  def _require_runtime_available(self, target: AdmittedTarget) -> None:
    if target.extension_id in ExtensionManager.RUNNING_EXTENSIONS:
      raise RegistryRuntimeConflictError(
        f"Legacy Extension {target.extension_id} already owns the canonical modules"
      )
    for running in self.running_extensions.values():
      if running.target.extension_id == target.extension_id:
        raise RegistryRuntimeConflictError(
          f"Registry Extension {target.extension_id} is already running"
        )

  async def _start(
    self,
    app: fastapi.FastAPI,
    installation: ExtensionInstallationModel,
    binding: ExtensionPeerBindingModel,
    target: AdmittedTarget,
  ) -> RunningRegistryExtension:
    coordinate = (binding.namespace, binding.name)
    existing = self.running_extensions.get(coordinate)
    if existing is not None:
      exact = (
        existing.binding.version,
        existing.binding.target_key,
        existing.binding.target_digest,
      )
      requested = (binding.version, binding.target_key, binding.target_digest)
      if exact != requested:
        raise RegistryRuntimeConflictError(
          "A different exact target already owns this Registry runtime"
        )
      return existing

    self._require_binding_version(installation, binding)
    self._require_runtime_available(target)
    manifest = target.verify_artifact()
    local_target = TargetRecord(
      target_key=binding.target_key,
      target_digest=binding.target_digest,
      artifact_format=manifest.artifact_format,
      entrypoint=manifest.entrypoint,
      conditions=manifest.conditions,
    )
    if not target_matches(local_target, self.platform_profile()):
      raise RegistryTargetNotCompatibleError(
        "Persisted admitted target is incompatible with this runtime profile"
      )
    modules = RegistryBundleModules(target)
    extension_class: type[ExtensionBase] | None = None
    schema_box: dict[str, dict[str, typing.Any]] = {}
    publication_snapshot = ExtensionPublicationSnapshot.capture(app)
    try:
      runtime_claim = ExtensionRuntimeClaim.acquire(target.extension_id)
    except ExtensionRuntimeClaimConflictError as error:
      raise RegistryRuntimeConflictError(str(error)) from error

    def persist_config(config: dict[str, typing.Any]) -> None:
      self.store.update_config(binding.namespace, binding.name, config)

    def stage_config_schema(schema: dict[str, typing.Any]) -> None:
      schema_box["value"] = schema

    try:
      extension_class = modules.load()
      runtime_record = ExtensionRuntimeRecord(
        extension_id=target.extension_id,
        config=dict(installation.config or {}),
        persist_config=persist_config,
        persist_config_schema=stage_config_schema,
      )
      extension_class.on_start(
        app,
        runtime_record,
        publication_snapshot=publication_snapshot,
      )
      modules.assert_admitted_origins()
      schema = schema_box.get("value")
      if schema is None:
        raise RegistryTargetAdmissionError("Extension did not publish its config schema")
      self.store.update_config_schema(binding.namespace, binding.name, schema)
    except Exception:
      if extension_class is not None and "__runtime_record__" in extension_class.__dict__:
        with contextlib.suppress(Exception):
          await extension_class.on_close()
        with contextlib.suppress(Exception):
          extension_class.unpublish()
        with contextlib.suppress(Exception):
          extension_class.release_runtime()
      with contextlib.suppress(Exception):
        publication_snapshot.rollback()
      with contextlib.suppress(Exception):
        modules.abort()
      runtime_claim.release()
      raise

    running = RunningRegistryExtension(
      binding=binding,
      target=target,
      extension_class=extension_class,
      modules=modules,
      runtime_claim=runtime_claim,
    )
    self.running_extensions[coordinate] = running
    return running

  async def _stop(self, running: RunningRegistryExtension) -> None:
    await running.extension_class.on_close()
    running.extension_class.unpublish()
    running.modules.unload()
    running.extension_class.release_runtime()
    running.runtime_claim.release()
    self.running_extensions.pop((running.binding.namespace, running.binding.name), None)

  async def _force_compensate(self, running: RunningRegistryExtension) -> list[Exception]:
    """Remove every observable runtime effect after binding persistence fails."""
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
      # Admission and the runtime lock prove this subtree belongs to this
      # uncommitted start. Abort is intentionally stronger than normal unload:
      # compensation must not leave executable modules behind.
      running.modules.abort()
    except Exception as error:
      failures.append(error)
    finally:
      running.extension_class.release_runtime()
      running.runtime_claim.release()
      self.running_extensions.pop(
        (running.binding.namespace, running.binding.name),
        None,
      )
    return failures

  async def enable(
    self,
    namespace: str,
    name: str,
    *,
    app: fastapi.FastAPI | None = None,
  ) -> ExtensionPeerBindingModel:
    self._validate_coordinate(namespace, name)
    runtime_app = app or self.fastapi_app
    if runtime_app is None:
      raise RegistryRuntimeConflictError("FastAPI app is required to enable an Extension")
    peer_id = ClientManager.get_current_client_id()

    async with self._runtime_lock:
      installation = self.get_installation(namespace, name)
      binding = self.store.get_binding(namespace, name, peer_id)
      if binding is not None:
        self._require_binding_version(installation, binding)
        target = self._admitted_catalog().require(
          binding.namespace,
          binding.name,
          binding.version,
          binding.target_key,
          binding.target_digest,
        )
        await self._start(runtime_app, installation, binding, target)
        return binding

      release = await asyncio.to_thread(
        self._resolve_release,
        namespace,
        name,
        installation.version,
      )
      selected = self._select_new_target(release)
      target = self._admitted_catalog().require(
        namespace,
        name,
        installation.version,
        selected.target_key,
        selected.target_digest,
      )
      self._require_registry_projection(selected, target)
      prospective = ExtensionPeerBindingModel(
        namespace=namespace,
        name=name,
        version=installation.version,
        peer_id=peer_id,
        target_key=selected.target_key,
        target_digest=selected.target_digest,
      )
      running = await self._start(runtime_app, installation, prospective, target)
      try:
        binding = self.store.create_binding(prospective)
      except Exception as persistence_error:
        compensation_failures = await self._force_compensate(running)
        if compensation_failures:
          raise ExceptionGroup(
            "Binding persistence and runtime compensation failed",
            [persistence_error, *compensation_failures],
          ) from persistence_error
        raise
      running.binding = binding
      return binding

  async def disable(self, namespace: str, name: str) -> ExtensionInstallationModel:
    self._validate_coordinate(namespace, name)
    peer_id = ClientManager.get_current_client_id()
    async with self._runtime_lock:
      installation = self.get_installation(namespace, name)
      binding = self.store.get_binding(namespace, name, peer_id)
      if binding is None:
        return installation
      self._require_binding_version(installation, binding)
      running = self.running_extensions.get((namespace, name))
      if running is not None:
        exact = (
          running.binding.version,
          running.binding.target_key,
          running.binding.target_digest,
        )
        persisted = (binding.version, binding.target_key, binding.target_digest)
        if exact != persisted:
          raise RegistryRuntimeConflictError(
            "Running target differs from the persisted peer binding"
          )
        await self._stop(running)
      self.store.delete_binding(namespace, name, peer_id)
      return installation

  async def start_enabled(self, app: fastapi.FastAPI) -> None:
    """Restore current-peer bindings without consulting mutable Registry state."""
    self.fastapi_app = app
    peer_id = ClientManager.get_current_client_id()
    async with self._runtime_lock:
      for binding in self.store.list_bindings_for_peer(peer_id):
        installation = self.get_installation(binding.namespace, binding.name)
        self._require_binding_version(installation, binding)
        target = self._admitted_catalog().require(
          binding.namespace,
          binding.name,
          binding.version,
          binding.target_key,
          binding.target_digest,
        )
        await self._start(app, installation, binding, target)

  async def close_running(self) -> None:
    failures: list[Exception] = []
    async with self._runtime_lock:
      for running in tuple(self.running_extensions.values()):
        try:
          await self._stop(running)
        except Exception as error:
          failures.append(error)
    if len(failures) == 1:
      raise failures[0]
    if failures:
      raise ExceptionGroup("Registry Extension shutdown failed", failures)


REGISTRY_EXTENSION_MANAGER = RegistryExtensionManager()


__all__ = [
  "AdmittedTarget",
  "AdmittedTargetCatalog",
  "REGISTRY_EXTENSION_MANAGER",
  "RegistryExtensionError",
  "RegistryExtensionManager",
  "RegistryInstallationConflictError",
  "RegistryInstallationNotFoundError",
  "RegistryResolutionError",
  "RegistryRuntimeConflictError",
  "RegistryTargetAdmissionError",
  "RegistryTargetNotCompatibleError",
]
