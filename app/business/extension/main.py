import abc
import typing
import fastapi
import sqlmodel
import importlib
import os
import tomllib
import json
from typing import Optional as Opt
from app.engine import SessionLocal
from app.database_contract.profile import BUILTIN_EXTENSIONS_BY_ID
from app.schemas.extension.main import ExtensionModel, ExtensionID
from libs.obsrv.main import get_logger

from .runtime import (
  ExtensionPublication,
  ExtensionPublicationSnapshot,
  ExtensionRuntimeClaim,
  ExtensionRuntimeRecord,
)


LOGGER = get_logger().getChild(__name__)


class EmptyConfig(sqlmodel.SQLModel): ...


ConfigTV = typing.TypeVar("ConfigTV", bound=sqlmodel.SQLModel)


class ExtensionBase(abc.ABC, typing.Generic[ConfigTV]):
  """InKCre Extension base class."""

  config: ConfigTV

  def __init_subclass__(
    cls,
    ext_id: ExtensionID,
    config_cls: type[ConfigTV],
    **kwargs,
  ) -> None:
    cls.__extid__ = ext_id
    # ConfigTV is bound by each concrete extension subclass; Python's type model
    # cannot represent a class attribute specialized by that subclass binding.
    cls.__configcls__ = config_cls  # pyrefly: ignore[no-access]
    cls.__configschema__ = config_cls.model_json_schema()
    return super().__init_subclass__(**kwargs)

  @classmethod
  def on_start(
    cls,
    app: fastapi.FastAPI,
    extension: ExtensionRuntimeRecord,
    publication_snapshot: ExtensionPublicationSnapshot | None = None,
  ) -> None:
    """Start and atomically publish one locally admitted Extension class."""
    snapshot = publication_snapshot or ExtensionPublicationSnapshot.capture(app)
    if cls.runtime_active():
      snapshot.rollback()
      raise RuntimeError(f"Extension runtime {cls.__extid__} is already active")
    if extension.extension_id != cls.__extid__:
      snapshot.rollback()
      raise RuntimeError(
        f"Runtime record {extension.extension_id} does not belong to {cls.__extid__}"
      )

    publication: ExtensionPublication | None = None
    setattr(cls, "__runtime_record__", extension)
    try:
      cls.config = cls.__configcls__(  # pyrefly: ignore[no-access]
        **(extension.config or {})
      )
      router = fastapi.APIRouter(prefix=f"/{cls.__extid__}")
      cls._register_apis(router)
      app.include_router(router, tags=["extension", cls.__extid__])

      cls._init_sources()
      cls._init_resolvers()
      publication = snapshot.finish()
      extension.persist_config_schema(dict(cls.__configschema__))
    except Exception:
      if publication is None:
        snapshot.rollback()
      else:
        publication.restore()
      raise

    setattr(cls, "__runtime_publication__", publication)
    LOGGER.info("Extension %s started.", cls.__extid__)

  @classmethod
  def _init_resolvers(cls): ...

  @classmethod
  def _init_sources(cls): ...

  @classmethod
  async def on_close(cls):
    record = typing.cast(
      ExtensionRuntimeRecord | None,
      cls.__dict__.get("__runtime_record__"),
    )
    if record is None:
      raise RuntimeError(f"Extension runtime {cls.__extid__} has no state record")
    config = typing.cast(sqlmodel.SQLModel, getattr(cls, "config"))
    record.persist_config(config.model_dump())
    LOGGER.info("Extension %s closed.", cls.__extid__)

  @classmethod
  def runtime_active(cls) -> bool:
    publication = typing.cast(
      ExtensionPublication | None,
      cls.__dict__.get("__runtime_publication__"),
    )
    return publication is not None and not publication.restored

  @classmethod
  def unpublish(cls) -> None:
    publication = typing.cast(
      ExtensionPublication | None,
      cls.__dict__.get("__runtime_publication__"),
    )
    if publication is not None:
      publication.restore()

  @classmethod
  def release_runtime(cls) -> None:
    """Forget class-local runtime state after teardown is fully successful."""
    for attribute in ("__runtime_publication__", "__runtime_record__"):
      if attribute in cls.__dict__:
        delattr(cls, attribute)

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
      cls.config = cls.__configcls__(**new_config)  # pyrefly: ignore[no-access]
    else:
      cls.config = new_config  # pyrefly: ignore[no-access]


class ExtensionManager:
  RUNNING_EXTENSIONS: dict[ExtensionID, type[ExtensionBase]] = dict()
  RUNNING_CLAIMS: dict[ExtensionID, ExtensionRuntimeClaim] = dict()
  FASTAPI_APP: fastapi.FastAPI | None = None

  @classmethod
  def start_enabled(cls, app: fastapi.FastAPI):
    """Start all extensions enabled for the current client."""
    cls.FASTAPI_APP = app
    for extension in cls.get_installed(enabled_only=True):
      cls.start(extension=extension)

  @classmethod
  async def close_running(cls):
    """Close all running extensions.

    It could involves closes of connections, so asynchronous.
    """
    failures: list[Exception] = []
    to_close = tuple(cls.RUNNING_EXTENSIONS)
    for extension_id in to_close:
      try:
        await cls.close(extension_id)
      except Exception as error:
        failures.append(error)
    if len(failures) == 1:
      raise failures[0]
    if failures:
      raise ExceptionGroup("Legacy Extension shutdown failed", failures)

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
    if app is None:
      raise ValueError("FastAPI app instance is required to start extension.")
    if extension is None and extid is not None:
      extension = cls.get(extid)
    if not extension:
      raise ValueError(f"Extension not provided or not found: {extid}")
    if extension.id in cls.RUNNING_EXTENSIONS:
      LOGGER.warning(f"Extension {extension.id} is already running.")
      return

    runtime_claim = ExtensionRuntimeClaim.acquire(extension.id)
    publication_snapshot = ExtensionPublicationSnapshot.capture(app)
    try:
      extension_module = importlib.import_module(f"extensions.{extension.id}")
    except Exception:
      try:
        publication_snapshot.rollback()
      finally:
        runtime_claim.release()
      raise
    extension_class = typing.cast(type[ExtensionBase], extension_module.Extension)
    if extension_class.runtime_active():
      try:
        publication_snapshot.rollback()
      finally:
        runtime_claim.release()
      raise RuntimeError(
        f"Extension runtime {extension.id} already owns the canonical module"
      )

    def persist_config(config: dict[str, typing.Any]) -> None:
      cls.save_config(extension.id, config)

    def persist_config_schema(schema: dict[str, typing.Any]) -> None:
      cls.save_config_schema(extension.id, schema)

    runtime_record = ExtensionRuntimeRecord(
      extension_id=extension.id,
      config=dict(extension.config or {}),
      persist_config=persist_config,
      persist_config_schema=persist_config_schema,
    )
    try:
      extension_class.on_start(
        app=app,
        extension=runtime_record,
        publication_snapshot=publication_snapshot,
      )
    except Exception:
      try:
        extension_class.release_runtime()
      finally:
        runtime_claim.release()
      raise
    cls.RUNNING_EXTENSIONS[extension.id] = extension_class
    cls.RUNNING_CLAIMS[extension.id] = runtime_claim

  @classmethod
  async def close(cls, extid: ExtensionID):
    """Close a specific extension."""
    extension_class = cls.RUNNING_EXTENSIONS.get(extid)
    if extension_class is None:
      LOGGER.warning(f"Extension {extid} is not running.")
      return

    await extension_class.on_close()
    extension_class.unpublish()
    extension_class.release_runtime()
    cls.RUNNING_EXTENSIONS.pop(extid, None)
    runtime_claim = cls.RUNNING_CLAIMS.pop(extid, None)
    if runtime_claim is not None:
      runtime_claim.release()

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
    """Enable an extension for the current client.

    Adds the current client ID to the extension's enabled list and starts it.
    """
    from app.business.client import ClientManager

    client_id = ClientManager.get_current_client_id()

    with SessionLocal() as db:
      extension = db.exec(
        sqlmodel.select(ExtensionModel).where(ExtensionModel.id == extid)
      ).first()

      if not extension:
        raise ValueError(f"Extension with id {extid} not found.")

      # Add client to enabled list if not already present
      current_enabled = set(extension.enabled)
      if client_id not in current_enabled:
        current_enabled.add(client_id)
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
    """Disable an extension for the current client.

    Removes the current client ID from the extension's enabled list and stops it.
    """
    from app.business.client import ClientManager

    client_id = ClientManager.get_current_client_id()

    with SessionLocal() as db:
      extension = db.exec(
        sqlmodel.select(ExtensionModel).where(ExtensionModel.id == extid)
      ).first()

      if not extension:
        raise ValueError(f"Extension with id {extid} not found.")

      # Remove client from enabled list
      current_enabled = set(extension.enabled)
      if client_id in current_enabled:
        current_enabled.discard(client_id)
        extension.enabled = list(current_enabled)
        db.add(extension)
        db.commit()
        db.refresh(extension)

      # Close extension if running
      if extid in cls.RUNNING_EXTENSIONS:
        await cls.close(extid)

      return extension

  @classmethod
  def get_installed(
    cls,
    enabled_only: bool = False,
  ) -> tuple[ExtensionModel, ...]:
    """Get installed extensions.

    :param enabled_only: If True, only return extensions enabled for the current client.
    """
    from app.business.client import ClientManager

    with SessionLocal() as db:
      query = sqlmodel.select(ExtensionModel)

      if enabled_only:
        client_id = ClientManager.get_current_client_id()
        # Filter: client_id must be in the enabled array
        enabled_column = typing.cast(typing.Any, ExtensionModel.enabled)
        query = query.where(enabled_column.any(client_id))

      return tuple(db.exec(query).all())

  @classmethod
  def get(cls, extid: ExtensionID) -> Opt[ExtensionModel]:
    """Get extension data by ID."""
    with SessionLocal() as db:
      return db.exec(
        sqlmodel.select(ExtensionModel).where(ExtensionModel.id == extid)
      ).first()

  @classmethod
  def save_config(
    cls,
    ext_id: ExtensionID,
    config: sqlmodel.SQLModel | dict,
  ) -> ExtensionModel:
    """Save extension config to database.

    Args:
        ext_id (ExtensionID):
        config (sqlmodel.SQLModel | dict):

    Returns:
        ExtensionModel: updated extension
    """
    with SessionLocal() as db:
      extension_model = db.exec(
        sqlmodel.select(ExtensionModel).where(ExtensionModel.id == ext_id)
      ).one()
      extension_model.config = (
        config.model_dump() if isinstance(config, sqlmodel.SQLModel) else config
      )
      db.add(extension_model)
      db.commit()
      db.refresh(extension_model)

      return extension_model

  @classmethod
  def save_config_schema(
    cls,
    ext_id: ExtensionID,
    config_schema: dict[str, typing.Any],
  ) -> ExtensionModel:
    """Persist the runtime-owned schema for one legacy extension record."""
    with SessionLocal() as db:
      extension_model = db.exec(
        sqlmodel.select(ExtensionModel).where(ExtensionModel.id == ext_id)
      ).one()
      extension_model.config_schema = config_schema
      db.add(extension_model)
      db.commit()
      db.refresh(extension_model)
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
