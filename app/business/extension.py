import abc
import typing
import fastapi
import sqlmodel
import importlib
import os
import tomllib
import shutil
import zipfile
import tempfile
import requests
import json
from typing import Optional as Opt
from app.engine import SessionLocal
from app.schemas.extension import ExtensionModel, ExtensionID
from app.logging_config import get_logger


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
        cls.__configcls__ = config_cls
        cls.__configschema__ = config_cls.model_json_schema()
        return super().__init_subclass__(**kwargs)

    @classmethod
    def on_start(cls, app: fastapi.FastAPI, extension: ExtensionModel):
        cls.config = cls.__configcls__(**(extension.config or {}))
        with SessionLocal() as db:
            extension.config_schema = cls.__configschema__
            db.add(extension)
            db.commit()

        router = fastapi.APIRouter(prefix=f"/{cls.__extid__}")
        cls._register_apis(router)
        app.include_router(router, tags=["extension", cls.__extid__])

        cls._init_sources()
        cls._init_resolvers()

        LOGGER.info(f"Extension {cls.__extid__} started.")

    @classmethod
    def _init_resolvers(cls): ...

    @classmethod
    def _init_sources(cls): ...

    @classmethod
    async def on_close(cls):
        ExtensionManager.save_config(ext_id=cls.__extid__, config=cls.config)
        LOGGER.info(f"Extension {cls.__extid__} closed.")

    @classmethod
    @abc.abstractmethod
    def _register_apis(cls, router: fastapi.APIRouter): ...

    @classmethod
    def update_config(cls, new_config: dict | ConfigTV):
        """Update extension configuration at runtime.

        :param new_config:
        """
        if isinstance(new_config, dict):
            cls.config = cls.__configcls__(**new_config)
        else:
            cls.config = new_config


class ExtensionManager:
    RUNNING_EXTENSIONS: dict[ExtensionID, type[ExtensionBase]] = dict()
    FASTAPI_APP: fastapi.FastAPI

    @classmethod
    def start_enabled(cls, app: fastapi.FastAPI):
        """Start all enabled entensions."""
        cls.FASTAPI_APP = app
        for extension in cls.get_installed():
            cls.start(extension=extension)

    @classmethod
    async def close_running(cls):
        """Close all running extensions.

        It could involves closes of connections, so asynchronous.
        """
        to_close = tuple(cls.RUNNING_EXTENSIONS.values())
        for extension_class in to_close:
            await extension_class.on_close()
            cls.RUNNING_EXTENSIONS.pop(extension_class.__extid__, None)

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
        extension_module = importlib.import_module(f"extensions.{extension.id}")
        extension_class = typing.cast(type[ExtensionBase], extension_module.Extension)

        if extension_class in cls.RUNNING_EXTENSIONS:
            LOGGER.warning(f"Extension {extension.id} is already running.")
        else:
            extension_class.on_start(
                app=app,
                extension=extension,
            )
            cls.RUNNING_EXTENSIONS[extension_class.__extid__] = extension_class

    @classmethod
    async def close(cls, extid: ExtensionID):
        """Close a specific extension."""
        extension_module = importlib.import_module(f"extensions.{extid}")
        extension_class = typing.cast(type[ExtensionBase], extension_module.Extension)
        if extension_class in cls.RUNNING_EXTENSIONS:
            await extension_class.on_close()
            cls.RUNNING_EXTENSIONS.pop(extension_class.__extid__, None)
        else:
            LOGGER.warning(f"Extension {extid} is not running.")

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
    def download(cls, extid: str, version: Opt[str] = None) -> ExtensionModel:
        """Download given extension to `extensions/`

        :param version: If None, download the latest version.
        """
        # Query PyPI API
        package_name = f"inkcre-ext-{extid}"
        pypi_url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(pypi_url)
        response.raise_for_status()
        pypi_data = response.json()

        # Determine version to download
        if version is None:
            version = pypi_data["info"]["version"]

        # Get release files for the specified version
        release_files = pypi_data["releases"].get(version, [])
        if not release_files:
            raise ValueError(f"Version {version} not found for {package_name}")

        # Find wheel file
        wheel_file = None
        for file_info in release_files:
            if file_info["packagetype"] == "bdist_wheel":
                wheel_file = file_info
                break

        if not wheel_file:
            raise ValueError(f"No wheel file found for {package_name} version {version}")

        # Download wheel file
        wheel_url = wheel_file["url"]
        wheel_response = requests.get(wheel_url)
        wheel_response.raise_for_status()

        # Create extensions directory if it doesn't exist
        extensions_dir = "extensions"
        os.makedirs(extensions_dir, exist_ok=True)

        # Extract wheel to temp directory first
        with tempfile.TemporaryDirectory() as temp_dir:
            wheel_path = os.path.join(temp_dir, wheel_file["filename"])
            with open(wheel_path, "wb") as f:
                f.write(wheel_response.content)

            # Extract wheel
            with zipfile.ZipFile(wheel_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            # Find the package directory (inkcre-ext-<extid> or <extid>)
            extracted_items = os.listdir(temp_dir)
            package_dir = None
            for item in extracted_items:
                item_path = os.path.join(temp_dir, item)
                if os.path.isdir(item_path) and (
                    item == package_name or item.startswith("inkcre_ext_")
                ):
                    package_dir = item_path
                    break

            if not package_dir:
                raise ValueError(f"Could not find package directory in wheel")

            # Prepare target directory
            target_dir = os.path.join(extensions_dir, extid)
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            os.makedirs(target_dir, exist_ok=True)

            # Move extension source files from inkcre_ext_<extid> to target_dir
            ext_src_dir = os.path.join(package_dir, extid.replace("-", "_"))
            if os.path.exists(ext_src_dir):
                for item in os.listdir(ext_src_dir):
                    src_path = os.path.join(ext_src_dir, item)
                    dst_path = os.path.join(target_dir, item)
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dst_path)
                    else:
                        shutil.copy2(src_path, dst_path)

            # Move dist-info directory
            dist_info_dir = None
            for item in os.listdir(package_dir):
                if item.endswith(".dist-info"):
                    dist_info_dir = os.path.join(package_dir, item)
                    break

            if dist_info_dir:
                target_dist_info = os.path.join(target_dir, os.path.basename(dist_info_dir))
                if os.path.exists(target_dist_info):
                    shutil.rmtree(target_dist_info)
                shutil.copytree(dist_info_dir, target_dist_info)

            # Move pyproject.toml if it exists in package_dir
            pyproject_src = os.path.join(package_dir, "pyproject.toml")
            if os.path.exists(pyproject_src):
                shutil.copy2(pyproject_src, os.path.join(target_dir, "pyproject.toml"))

        # Return extension model with downloaded info
        nickname, _ = cls._read_metadata(target_dir)

        return ExtensionModel(
            id=extid,
            version=version or "0.0.0",
            nickname=nickname,
            config={},
            disabled=True,
        )

    @classmethod
    def install(cls, extid: ExtensionID, version: Opt[str] = None) -> ExtensionModel:
        """Install extension. Install if not yet."""
        with SessionLocal() as db:
            # Check if extension already installed
            existing = db.exec(
                sqlmodel.select(ExtensionModel).where(ExtensionModel.id == extid)
            ).first()

            if existing:
                return existing

            # Install
            extension = cls.download(extid, version=version)
            db.add(extension)
            db.commit()
            db.refresh(extension)

            return extension

    @classmethod
    async def set_disabled(cls, extid: ExtensionID, disabled: bool) -> ExtensionModel:
        """Enable or disable an extension."""
        with SessionLocal() as db:
            extension = db.exec(
                sqlmodel.select(ExtensionModel).where(ExtensionModel.id == extid)
            ).first()

            if not extension:
                raise ValueError(f"Extension with id {extid} not found.")

            extension.disabled = disabled
            db.add(extension)
            db.commit()
            db.refresh(extension)

            if disabled:
                await cls.close(extid)
            else:
                cls.start(extid)

            return extension

    @classmethod
    def get_installed(cls, disabled: Opt[bool] = False) -> tuple[ExtensionModel, ...]:
        """Get installed extensions.

        :param disabled: If True, include disabled extensions; otherwise, only enabled ones.
        """
        with SessionLocal() as db:
            return tuple(
                db.exec(
                    sqlmodel.select(ExtensionModel).where(
                        disabled is None or ExtensionModel.disabled == disabled
                    )
                ).all()
            )

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

                        # Skip if we couldn't read any metadata
                        if nickname is None and version is None:
                            LOGGER.warning(
                                f"Skipping extension {ext_id}: no valid metadata found"
                            )
                            continue

                        local_extensions.add(ext_id)
                        local_count += 1

                        # Use default version if not found in metadata
                        if version is None:
                            version = "0.1.0"
                            LOGGER.info(
                                f"Using default version {version} for extension {ext_id}"
                            )

                        existing = db.exec(
                            sqlmodel.select(ExtensionModel).where(
                                ExtensionModel.id == ext_id
                            )
                        ).first()
                        if existing:
                            LOGGER.info(
                                f"Updating existing extension {ext_id}: version={version}, nickname={nickname}"
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
                                disabled=True,
                            )
                            db.add(new_ext)
                            new_count += 1

            db.commit()
            LOGGER.info(
                f"Local sync completed: {local_count} local extensions found, {updated_count} updated, {new_count} added"
            )

            # Check for extensions in database but not locally installed
            all_db_extensions = db.exec(sqlmodel.select(ExtensionModel)).all()
            db_only_count = 0
            download_success_count = 0
            download_error_count = 0

            LOGGER.info(f"Checking database extensions for missing local installations")

            for db_ext in all_db_extensions:
                if db_ext.id not in local_extensions:
                    db_only_count += 1
                    LOGGER.info(
                        f"Extension {db_ext.id} exists in database but not locally, attempting download"
                    )
                    # Download missing extension
                    try:
                        cls.download(db_ext.id, version=db_ext.version)
                        download_success_count += 1
                        LOGGER.info(
                            f"Successfully downloaded extension {db_ext.id} version {db_ext.version}"
                        )
                    except Exception as e:
                        download_error_count += 1
                        # Log error but continue syncing other extensions
                        LOGGER.error(
                            f"Failed to download extension {db_ext.id}: {e}", exc_info=True
                        )

            LOGGER.info(
                f"Database sync completed: {db_only_count} database-only extensions found, "
                f"{download_success_count} successfully downloaded, {download_error_count} download failures"
            )
            LOGGER.info("Extension synchronization completed successfully")
