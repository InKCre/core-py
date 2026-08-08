import abc
import typing
import fastapi
import pydantic
import sqlmodel
import importlib
import os
import tomllib
import json
from typing import Optional as Opt
from app.engine import SessionLocal
from app.configuration import ConfigContract
from app.database_contract.profile import BUILTIN_EXTENSIONS_BY_ID
from app.schemas.ai import JSONValue
from app.schemas.extension.main import (
  DisableExtensionCommand,
  EnableExtensionCommand,
  ExtensionID,
  ExtensionManagementCommand,
  ExtensionModel,
  PatchExtensionConfigCommand,
)
from app.schemas.peer import PeerProtocolRequest, PeerProtocolResponse, PeerRef
from app.middleware import require_peer_jwt
from .routing import ExtensionRouteMount
from libs.obsrv.main import get_logger


LOGGER = get_logger().getChild(__name__)
EXTENSION_MANAGEMENT_CAPABILITY = "core.extension.management.v1"


class ExtensionDelegationError(RuntimeError):
  pass


class EmptyConfig(sqlmodel.SQLModel): ...


ConfigTV = typing.TypeVar("ConfigTV", bound=sqlmodel.SQLModel)


class ExtensionBase(abc.ABC, typing.Generic[ConfigTV]):
  """InKCre Extension base class."""

  config: ConfigTV
  __configcontract__: ConfigContract[ConfigTV]

  def __init_subclass__(
    cls,
    ext_id: ExtensionID,
    config_cls: type[ConfigTV],
    **kwargs,
  ) -> None:
    cls.__extid__ = ext_id
    # ConfigTV is bound by each concrete extension subclass; Python's type model
    # cannot represent a class attribute specialized by that subclass binding.
    cls.__configcontract__ = ConfigContract(config_cls)  # pyrefly: ignore[no-access]
    return super().__init_subclass__(**kwargs)

  @classmethod
  def on_start(cls, extension: ExtensionModel) -> fastapi.APIRouter:
    cls.config = cls.validate_config(extension.config or {})  # pyrefly: ignore[no-access]

    router = fastapi.APIRouter(
      prefix=f"/{cls.__extid__}",
      tags=["extension", cls.__extid__],
      dependencies=cls.api_dependencies(),
    )
    cls._register_apis(router)

    cls._init_sources()

    LOGGER.info(f"Extension {cls.__extid__} started.")
    return router

  @classmethod
  def api_dependencies(cls) -> list[typing.Any]:
    """Return root API dependencies; override with [] to compose extension auth."""
    return [fastapi.Depends(require_peer_jwt)]

  @classmethod
  def load_decoders(cls) -> None:
    """Load persisted-content decoders independently of live API/source state."""
    cls._init_resolvers()

  @classmethod
  def _init_resolvers(cls): ...

  @classmethod
  def _init_sources(cls): ...

  @classmethod
  async def on_close(cls):
    LOGGER.info(f"Extension {cls.__extid__} closed.")

  @classmethod
  @abc.abstractmethod
  def _register_apis(cls, router: fastapi.APIRouter):
    """Register API endpoints for the extension here.

    - Do not register API bypass or duplicate with the core APIs.
    """

  @classmethod
  def update_config(cls, new_config: dict | ConfigTV):
    """Update extension configuration at runtime.

    :param new_config:
    """
    if isinstance(new_config, dict):
      cls.config = cls.__configcontract__.validate(new_config)  # pyrefly: ignore[no-access]
    else:
      cls.config = new_config  # pyrefly: ignore[no-access]

  @classmethod
  def validate_config(cls, config: dict) -> ConfigTV:
    """Validate and normalize persisted configuration for this extension."""
    return cls.__configcontract__.validate(config)  # pyrefly: ignore[missing-attribute, bad-return]

  @classmethod
  def prepare_config_patch(
    cls,
    current: dict[str, typing.Any],
    patch: dict[str, typing.Any],
  ) -> ConfigTV:
    """Validate a shallow patch through the shared config mechanics."""
    return cls.__configcontract__.prepare_patch(current, patch)  # pyrefly: ignore[missing-attribute, bad-return]

  @classmethod
  def config_schema(cls) -> dict:
    """Return optional UI metadata derived from the authoritative config model."""
    return cls.__configcontract__.json_schema()  # pyrefly: ignore[missing-attribute]


class ExtensionManager:
  RUNNING_EXTENSIONS: dict[ExtensionID, type[ExtensionBase]] = dict()
  ROUTE_MOUNTS: dict[ExtensionID, ExtensionRouteMount] = dict()
  FASTAPI_APP: fastapi.FastAPI | None = None

  @classmethod
  def start_enabled(cls, app: fastapi.FastAPI):
    """Start all extensions enabled for the current Peer."""
    cls.FASTAPI_APP = app
    for extension in cls.get_installed(enabled_only=True):
      cls.start(extension=extension)

  @classmethod
  def load_installed_decoders(cls) -> None:
    """Make decoders for installed artifacts available even while disabled."""
    for extension in cls.get_installed():
      cls._load_extension_class(extension.id).load_decoders()

  @classmethod
  async def close_running(cls):
    """Close all running extensions.

    It could involves closes of connections, so asynchronous.
    """
    to_close = tuple(cls.RUNNING_EXTENSIONS)
    for extid in to_close:
      await cls.close(extid)

  @classmethod
  def start(
    cls,
    extid: Opt[ExtensionID] = None,
    extension: Opt[ExtensionModel] = None,
    app: Opt[fastapi.FastAPI] = None,
  ):
    """Start a specific extension."""
    if app is None:
      app = cls.FASTAPI_APP
    else:
      cls.FASTAPI_APP = app
    if app is None:
      raise ValueError("FastAPI app instance is required to start extension.")
    if extension is None and extid is not None:
      extension = cls.get(extid)
    if not extension:
      raise ValueError(f"Extension not provided or not found: {extid}")
    extension_class = cls._load_extension_class(extension.id)

    if extension.id in cls.RUNNING_EXTENSIONS:
      LOGGER.warning(f"Extension {extension.id} is already running.")
    else:
      extension_class.load_decoders()
      cls._save_config_schema(extension.id, extension_class.config_schema())
      router = extension_class.on_start(extension=extension)
      mount = ExtensionRouteMount(app=app, router=router)
      mount.publish()
      cls.ROUTE_MOUNTS[extension.id] = mount
      cls.RUNNING_EXTENSIONS[extension_class.__extid__] = extension_class

  @classmethod
  async def close(cls, extid: ExtensionID):
    """Close a specific extension."""
    extension_class = cls.RUNNING_EXTENSIONS.get(extid)
    if extension_class is None:
      LOGGER.warning(f"Extension {extid} is not running.")
      return

    mount = cls.ROUTE_MOUNTS.get(extid)
    if mount is not None:
      mount.unpublish()

    # Keep the runtime entry after a close failure so a later disable/close can retry.
    await extension_class.on_close()
    cls.ROUTE_MOUNTS.pop(extid, None)
    cls.RUNNING_EXTENSIONS.pop(extid, None)

  @classmethod
  def _load_extension_class(cls, extid: ExtensionID) -> type[ExtensionBase]:
    extension_module = importlib.import_module(f"extensions.{extid}")
    return typing.cast(type[ExtensionBase], extension_module.Extension)

  @classmethod
  def _save_config_schema(cls, extid: ExtensionID, config_schema: dict) -> None:
    with SessionLocal() as db:
      extension = db.exec(
        sqlmodel.select(ExtensionModel).where(ExtensionModel.id == extid)
      ).first()
      if extension is None or extension.config_schema == config_schema:
        return
      extension.config_schema = config_schema
      db.add(extension)
      db.commit()

  @classmethod
  def _read_metadata(cls, ext_path: str) -> tuple[Opt[str], Opt[str]]:
    """Read extension metadata (nickname, version) from a local extension
    directory.

    :param ext_path: Path to the extension directory
    :return: Tuple of (nickname, version). Returns (None, None) if metadata
             cannot be read.
    """
    nickname = None
    version = None

    # Try to read metadata from pyproject.toml first
    pyproject_path = os.path.join(ext_path, "pyproject.toml")
    if os.path.exists(pyproject_path):
      try:
        with open(pyproject_path, "rb") as f:
          data = tomllib.load(f)
        inkcre_ext = data.get("tool", {}).get("inkcre-ext", {})
        nickname = inkcre_ext.get("nickname", None)
        version = data.get("project", {}).get("version", None)
        return nickname, version
      except Exception:
        # Continue to try metadata.json
        pass

    # Fall back to reading metadata.json from dist-info directory
    metadata_json_path = None
    for dist_info_item in os.listdir(ext_path):
      if dist_info_item.endswith(".dist-info"):
        metadata_json_path = os.path.join(ext_path, dist_info_item, "metadata.json")
        break

    if metadata_json_path and os.path.exists(metadata_json_path):
      try:
        with open(metadata_json_path, "r", encoding="utf-8") as f:
          metadata = json.load(f)
        ext_meta = metadata.get("extensions", {}).get("inkcre-ext", {})
        nickname = ext_meta.get("nickname", None)
        version = metadata.get("version", None)
        return nickname, version
      except Exception:
        # Skip if metadata.json is also invalid
        pass

    return None, None

  @classmethod
  def install(cls, extid: ExtensionID, version: Opt[str] = None) -> ExtensionModel:
    """Register a checked-in extension without downloading runtime code."""
    extension_path = os.path.join("extensions", extid)
    if not os.path.isdir(extension_path):
      raise ValueError(f"Extension {extid} is not part of this artifact")

    nickname, local_version = cls._read_metadata(extension_path)
    if nickname is None and local_version is None:
      raise ValueError(f"Extension {extid} has no valid local metadata")
    local_version = local_version or "0.1.0"
    if version is not None and version != local_version:
      raise ValueError(f"Extension {extid} version {version} is not part of this artifact")

    with SessionLocal() as db:
      existing = db.exec(
        sqlmodel.select(ExtensionModel).where(ExtensionModel.id == extid)
      ).first()
      if existing:
        existing.version = local_version
        existing.nickname = nickname
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

      extension = ExtensionModel(
        id=extid,
        version=local_version,
        nickname=nickname,
        config={},
        enabled=[],
      )
      db.add(extension)
      db.commit()
      db.refresh(extension)

      return extension

  @classmethod
  async def enable(cls, extid: ExtensionID) -> ExtensionModel:
    """Enable an extension for the current Peer.

    Adds the current Peer ID to the extension's enabled list and starts it.
    """
    from app.business.peer import PeerManager

    peer = PeerManager.get_current_peer_ref()

    with SessionLocal() as db:
      extension = db.exec(
        sqlmodel.select(ExtensionModel).where(ExtensionModel.id == extid)
      ).first()

      if not extension:
        raise ValueError(f"Extension with id {extid} not found.")

      current_enabled = set(extension.enabled)
      if peer not in current_enabled:
        current_enabled.add(peer)
        extension.enabled = list(current_enabled)
        db.add(extension)
        db.commit()
        db.refresh(extension)

      # Start extension if not already running
      if extid not in cls.RUNNING_EXTENSIONS:
        cls.start(extid)

      return extension

  @classmethod
  async def disable(cls, extid: ExtensionID) -> ExtensionModel:
    """Disable an extension for the current Peer.

    Removes the current Peer ID from the extension's enabled list and stops it.
    """
    from app.business.peer import PeerManager

    peer = PeerManager.get_current_peer_ref()

    with SessionLocal() as db:
      extension = db.exec(
        sqlmodel.select(ExtensionModel).where(ExtensionModel.id == extid)
      ).first()

      if not extension:
        raise ValueError(f"Extension with id {extid} not found.")

      current_enabled = set(extension.enabled)
      if peer in current_enabled:
        current_enabled.discard(peer)
        extension.enabled = list(current_enabled)
        db.add(extension)
        db.commit()
        db.refresh(extension)

      # Close extension if running
      if extid in cls.RUNNING_EXTENSIONS:
        await cls.close(extid)

      return extension

  @classmethod
  async def manage(
    cls,
    command: ExtensionManagementCommand,
    *,
    route_to_peer: PeerRef,
  ) -> ExtensionModel:
    """Execute one Extension command on one exact Peer."""
    from app.business.peer import PeerManager

    if route_to_peer == PeerManager.get_current_peer_ref():
      return await cls.manage_local(command)

    payload = PeerProtocolRequest(
      body=typing.cast(
        JSONValue,
        command.model_dump(mode="json"),
      )
    )
    result = await PeerManager.delegate(
      EXTENSION_MANAGEMENT_CAPABILITY,
      typing.cast(JSONValue, payload.model_dump(mode="json", exclude_unset=True)),
      route_to_peer=route_to_peer,
    )
    try:
      response = PeerProtocolResponse.model_validate(result)
      if response.status != 200 or "body" not in response.model_fields_set:
        raise ExtensionDelegationError(
          f"Extension management Peer returned HTTP {response.status}"
        )
      return ExtensionModel.model_validate(response.body)
    except pydantic.ValidationError as error:
      raise ExtensionDelegationError(
        "Extension management Peer returned an invalid response"
      ) from error

  @classmethod
  async def manage_local(
    cls,
    command: ExtensionManagementCommand,
  ) -> ExtensionModel:
    """Execute one already-validated command without entering delegation."""
    if isinstance(command, EnableExtensionCommand):
      return await cls.enable(command.extension)
    if isinstance(command, DisableExtensionCommand):
      return await cls.disable(command.extension)
    if isinstance(command, PatchExtensionConfigCommand):
      updated = cls.update_config(command.extension, command.patch)
      if updated is None:
        raise ValueError(f"Extension with id {command.extension} not found.")
      return updated
    typing.assert_never(command)

  @classmethod
  def get_installed(
    cls,
    enabled_only: bool = False,
  ) -> tuple[ExtensionModel, ...]:
    """Get installed extensions.

    :param enabled_only: If True, only return extensions enabled for the current Peer.
    """
    from app.business.peer import PeerManager

    with SessionLocal() as db:
      query = sqlmodel.select(ExtensionModel)

      if enabled_only:
        peer = PeerManager.get_current_peer_ref()
        enabled_column = typing.cast(typing.Any, ExtensionModel.enabled)
        query = query.where(enabled_column.any(peer))

      return tuple(db.exec(query).all())

  @classmethod
  def get(cls, extid: ExtensionID) -> Opt[ExtensionModel]:
    """Get extension data by ID."""
    with SessionLocal() as db:
      return db.exec(
        sqlmodel.select(ExtensionModel).where(ExtensionModel.id == extid)
      ).first()

  @classmethod
  def update_config(
    cls,
    extid: ExtensionID,
    patch: dict[str, typing.Any],
  ) -> ExtensionModel | None:
    """Validate a shallow config patch, persist it, then apply it live."""
    with SessionLocal() as db:
      extension_model = db.exec(
        sqlmodel.select(ExtensionModel).where(ExtensionModel.id == extid)
      ).first()
      if extension_model is None:
        return None

      extension_class = cls._load_extension_class(extid)
      validated = extension_class.prepare_config_patch(
        extension_model.config or {},
        patch,
      )
      extension_model.config = validated.model_dump(mode="json")
      extension_model.config_schema = extension_class.config_schema()
      db.add(extension_model)
      db.commit()
      db.refresh(extension_model)

    running_class = cls.RUNNING_EXTENSIONS.get(extid)
    if running_class is not None:
      running_class.update_config(validated)

    return extension_model

  @classmethod
  def sync(cls):
    """Sync locally installed extensions with database (bi-directional)."""
    LOGGER.info("Starting extension synchronization")

    extensions_dir = "extensions"
    os.makedirs(extensions_dir, exist_ok=True)

    with SessionLocal() as db:
      # Get all locally installed extensions
      local_extensions = set()
      local_count = 0
      updated_count = 0
      new_count = 0

      LOGGER.info(f"Scanning local extensions directory: {extensions_dir}")

      if os.path.exists(extensions_dir):
        for item in os.listdir(extensions_dir):
          ext_path = os.path.join(extensions_dir, item)
          if os.path.isdir(ext_path):
            ext_id = item  # Folder name is the extension ID
            LOGGER.debug(f"Processing local extension: {ext_id}")

            nickname, version = cls._read_metadata(ext_path)
            builtin = BUILTIN_EXTENSIONS_BY_ID.get(ext_id)
            if builtin is not None:
              nickname = builtin.nickname
              version = builtin.version

            # Skip if we couldn't read any metadata
            if nickname is None and version is None:
              LOGGER.warning(f"Skipping extension {ext_id}: no valid metadata found")
              continue

            local_extensions.add(ext_id)
            local_count += 1

            # Use default version if not found in metadata
            if version is None:
              version = "0.1.0"
              LOGGER.info(f"Using default version {version} for extension {ext_id}")

            existing = db.exec(
              sqlmodel.select(ExtensionModel).where(ExtensionModel.id == ext_id)
            ).first()
            if existing:
              LOGGER.info(
                "Updating existing extension %s: version=%s, nickname=%s",
                ext_id,
                version,
                nickname,
              )
              existing.version = version
              existing.nickname = nickname
              db.add(existing)
              updated_count += 1
            else:
              LOGGER.info(
                f"Adding new extension {ext_id}: version={version}, nickname={nickname}"
              )
              new_ext = ExtensionModel(
                id=ext_id,
                version=version,
                nickname=nickname,
                enabled=[],
              )
              db.add(new_ext)
              new_count += 1

      db.commit()
      LOGGER.info(
        "Local sync completed: %d local extensions found, %d updated, %d added",
        local_count,
        updated_count,
        new_count,
      )

      # Runtime artifacts are immutable. Database-only records are never downloaded.
      all_db_extensions = db.exec(sqlmodel.select(ExtensionModel)).all()
      db_only = sorted(
        extension.id
        for extension in all_db_extensions
        if extension.id not in local_extensions
      )
      if db_only:
        LOGGER.warning(
          "Ignoring database-only extensions absent from this artifact: %s",
          ", ".join(db_only),
        )
      LOGGER.info("Extension synchronization completed successfully")
