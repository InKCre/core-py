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


class EmptyConfig(sqlmodel.SQLModel): ...


ConfigTV = typing.TypeVar("ConfigTV", bound=sqlmodel.SQLModel)
StateTV = typing.TypeVar("StateTV", bound=sqlmodel.SQLModel)


class ExtensionBase(abc.ABC, typing.Generic[ConfigTV, StateTV]):
    """InKCre Extension base class."""

    config: ConfigTV
    state: StateTV

    def __init_subclass__(
        cls,
        ext_id: ExtensionID,
        config_cls: type[ConfigTV],
        state_cls: type[StateTV],
        **kwargs,
    ) -> None:
        cls.__extid__ = ext_id
        cls.__configcls__ = config_cls
        cls.__statecls__ = state_cls
        return super().__init_subclass__(**kwargs)

    @classmethod
    def on_start(cls, app: fastapi.FastAPI, config: dict, state: dict):
        cls.config = cls.__configcls__(**config)
        cls.state = cls.__statecls__(**state)

        router = fastapi.APIRouter(prefix=f"/{cls.__extid__}")
        cls._register_apis(router)
        app.include_router(router, tags=["extension", cls.__extid__])

        cls._init_sources()
        cls._init_resolvers()

    @classmethod
    def _init_resolvers(cls): ...

    @classmethod
    def _init_sources(cls): ...

    @classmethod
    async def on_close(cls):
        ExtensionManager.save_config_and_state(
            ext_id=cls.__extid__, config=cls.config, state=cls.state
        )

    @classmethod
    @abc.abstractmethod
    def _register_apis(cls, router: fastapi.APIRouter): ...


class ExtensionManager:
    extention_classes: list[type[ExtensionBase]] = []

    @classmethod
    def start_all(cls, app: fastapi.FastAPI):
        """Start enabled entensions."""
        for extension in cls.get_installed():
            extension_module = importlib.import_module(f"extensions.{extension.id}")
            extension_class = typing.cast(type[ExtensionBase], extension_module.Extension)
            cls.extention_classes.append(extension_class)

            extension_class.on_start(
                app=app, config=extension.config or {}, state=extension.state or {}
            )

    @classmethod
    async def close_all(cls):
        """Close all extensions.

        It could involves closes of connections, so asynchronous.
        """
        for extension_class in cls.extention_classes:
            await extension_class.on_close()

    @classmethod
    def read_metadata(cls, ext_path: str) -> tuple[Opt[str], Opt[str]]:
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
        nickname, _ = cls.read_metadata(target_dir)

        return ExtensionModel(
            id=extid,
            version=version or "0.0.0",
            nickname=nickname,
            config={},
            state={},
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

    # TODO make into enable, disable; and apply immediate effect
    @classmethod
    def set_disabled(cls, extid: ExtensionID, disabled: bool) -> ExtensionModel:
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
    def save_config_and_state(
        cls,
        ext_id: ExtensionID,
        config: Opt[sqlmodel.SQLModel | dict] = None,
        state: Opt[sqlmodel.SQLModel | dict] = None,
    ) -> ExtensionModel:
        with SessionLocal() as db:
            extension_model = db.exec(
                sqlmodel.select(ExtensionModel).where(ExtensionModel.id == ext_id)
            ).one()
            if config:
                extension_model.config = (
                    config.model_dump() if isinstance(config, sqlmodel.SQLModel) else config
                )
            if state:
                extension_model.state = (
                    state.model_dump() if isinstance(state, sqlmodel.SQLModel) else state
                )
            db.add(extension_model)
            db.commit()

        return extension_model

    @classmethod
    def update_config(cls, extension_id: ExtensionID, config: dict) -> Opt[dict]:
        """Update extension config with a dict.

        Returns the updated config, or None if extension not found.
        """
        with SessionLocal() as db:
            extension_model = db.exec(
                sqlmodel.select(ExtensionModel).where(ExtensionModel.id == extension_id)
            ).first()

            if not extension_model:
                return None

            extension_model.config = config
            db.add(extension_model)
            db.commit()
            db.refresh(extension_model)

            return extension_model.config

    @classmethod
    def sync(cls):
        """Sync locally installed extensions with database (bi-directional)."""
        extensions_dir = "extensions"
        os.makedirs(extensions_dir, exist_ok=True)

        with SessionLocal() as db:
            # Get all locally installed extensions
            local_extensions = set()
            if os.path.exists(extensions_dir):
                for item in os.listdir(extensions_dir):
                    ext_path = os.path.join(extensions_dir, item)
                    if os.path.isdir(ext_path):
                        ext_id = item  # Folder name is the extension ID
                        nickname, version = cls.read_metadata(ext_path)

                        # Skip if we couldn't read any metadata
                        if nickname is None and version is None:
                            continue

                        local_extensions.add(ext_id)

                        # Use default version if not found in metadata
                        if version is None:
                            version = "0.1.0"

                        existing = db.exec(
                            sqlmodel.select(ExtensionModel).where(
                                ExtensionModel.id == ext_id
                            )
                        ).first()
                        if existing:
                            existing.version = version
                            existing.nickname = nickname
                            db.add(existing)
                        else:
                            new_ext = ExtensionModel(
                                id=ext_id,
                                version=version,
                                nickname=nickname,
                                disabled=True,
                            )
                            db.add(new_ext)

            db.commit()

            # Check for extensions in database but not locally installed
            all_db_extensions = db.exec(sqlmodel.select(ExtensionModel)).all()
            for db_ext in all_db_extensions:
                if db_ext.id not in local_extensions:
                    # Download missing extension
                    try:
                        cls.download(db_ext.id, version=db_ext.version)
                    except Exception as e:
                        # Log error but continue syncing other extensions
                        print(f"Failed to download extension {db_ext.id}: {e}")
