"""Extension Module's API Endpoints"""

__all__ = ["REGISTRY_ROUTER", "ROUTER"]

import typing
import fastapi
import pydantic
from app.business.extension.main import ExtensionManager
from app.business.extension.registry import (
  REGISTRY_EXTENSION_MANAGER,
  RegistryExtensionError,
  RegistryInstallationConflictError,
  RegistryInstallationNotFoundError,
  RegistryResolutionError,
  RegistryRuntimeConflictError,
  RegistryTargetAdmissionError,
  RegistryTargetNotCompatibleError,
)
from app.schemas.extension.registry import (
  ExtensionInstallationModel,
  ExtensionPeerBindingModel,
)
from app.schemas.extension.main import ExtensionModel, ExtensionID

ROUTER = fastapi.APIRouter(
  prefix="/extensions",
  tags=["extension"],
)

REGISTRY_ROUTER = fastapi.APIRouter(
  prefix="/extension-installations",
  tags=["extension-installation"],
)


def _raise_registry_http_error(error: RegistryExtensionError) -> typing.NoReturn:
  if isinstance(error, RegistryInstallationNotFoundError):
    status_code = fastapi.status.HTTP_404_NOT_FOUND
  elif isinstance(error, RegistryResolutionError):
    status_code = fastapi.status.HTTP_502_BAD_GATEWAY
  elif isinstance(
    error,
    (
      RegistryInstallationConflictError,
      RegistryRuntimeConflictError,
      RegistryTargetAdmissionError,
      RegistryTargetNotCompatibleError,
    ),
  ):
    status_code = fastapi.status.HTTP_409_CONFLICT
  else:
    status_code = fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR
  raise fastapi.HTTPException(status_code=status_code, detail=str(error)) from error


@ROUTER.get("")
def get_extensions() -> tuple[ExtensionModel, ...]:
  """List all installed extensions"""
  return ExtensionManager.get_installed()


@ROUTER.post("/{extid}")
def install_extension(
  extid: ExtensionID,
  disabled: bool = fastapi.Query(default=False),
  version: str | None = fastapi.Query(default=None),
) -> ExtensionModel:
  """Register an extension that is already included in this artifact."""
  try:
    return ExtensionManager.install(extid, version=version)
  except ValueError as error:
    raise fastapi.HTTPException(
      status_code=fastapi.status.HTTP_409_CONFLICT,
      detail=str(error),
    ) from error


@ROUTER.post("/{extid}/enable")
async def enable_extension(extid: ExtensionID) -> ExtensionModel:
  """启用插件 (Enable extension for current client)"""
  try:
    return await ExtensionManager.enable(extid)
  except ValueError:
    raise fastapi.HTTPException(
      status_code=fastapi.status.HTTP_404_NOT_FOUND,
      detail=f"Extension with id {extid} not found.",
    )


@ROUTER.post("/{extid}/disable")
async def disable_extension(extid: ExtensionID) -> ExtensionModel:
  """禁用插件 (Disable extension for current client)"""
  try:
    return await ExtensionManager.disable(extid)
  except ValueError:
    raise fastapi.HTTPException(
      status_code=fastapi.status.HTTP_404_NOT_FOUND,
      detail=f"Extension with id {extid} not found.",
    )


@ROUTER.put("/{extid}/config")
def update_extension_config(
  extid: ExtensionID, body: dict[str, typing.Any] = fastapi.Body(...)
) -> ExtensionModel:
  """编辑插件配置 (Edit extension configuration)

  编辑成功将会立刻应用到插件中（如果正在运行）
  """
  updated_ext = ExtensionManager.save_config(extid, body)

  if updated_ext is None:
    raise fastapi.HTTPException(
      status_code=fastapi.status.HTTP_404_NOT_FOUND,
      detail=f"Extension with id {extid} not found.",
    )

  ext_cls = ExtensionManager.RUNNING_EXTENSIONS.get(extid, None)
  if ext_cls is not None:
    ext_cls.update_config(updated_ext.config)

  return updated_ext


@REGISTRY_ROUTER.get("")
def list_registry_installations() -> tuple[ExtensionInstallationModel, ...]:
  return REGISTRY_EXTENSION_MANAGER.list_installations()


@REGISTRY_ROUTER.get("/{namespace}/{name}")
def get_registry_installation(namespace: str, name: str) -> ExtensionInstallationModel:
  try:
    return REGISTRY_EXTENSION_MANAGER.get_installation(namespace, name)
  except RegistryExtensionError as error:
    _raise_registry_http_error(error)


@REGISTRY_ROUTER.post("/{namespace}/{name}")
def install_registry_extension(
  namespace: str,
  name: str,
  version: str = fastapi.Query(...),
) -> ExtensionInstallationModel:
  """Install one exact published release without enabling any peer."""
  try:
    return REGISTRY_EXTENSION_MANAGER.install(namespace, name, version)
  except RegistryExtensionError as error:
    _raise_registry_http_error(error)


@REGISTRY_ROUTER.delete("/{namespace}/{name}", status_code=204)
def uninstall_registry_extension(namespace: str, name: str) -> fastapi.Response:
  try:
    REGISTRY_EXTENSION_MANAGER.uninstall(namespace, name)
  except RegistryExtensionError as error:
    _raise_registry_http_error(error)
  return fastapi.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)


@REGISTRY_ROUTER.put("/{namespace}/{name}/config")
def update_registry_extension_config(
  namespace: str,
  name: str,
  body: dict[str, typing.Any] = fastapi.Body(...),
) -> ExtensionInstallationModel:
  try:
    return REGISTRY_EXTENSION_MANAGER.update_config(namespace, name, body)
  except pydantic.ValidationError as error:
    raise fastapi.HTTPException(
      status_code=fastapi.status.HTTP_422_UNPROCESSABLE_CONTENT,
      detail=error.errors(include_url=False, include_context=False),
    ) from error
  except RegistryExtensionError as error:
    _raise_registry_http_error(error)


@REGISTRY_ROUTER.post("/{namespace}/{name}/enable")
async def enable_registry_extension(
  namespace: str,
  name: str,
) -> ExtensionPeerBindingModel:
  try:
    return await REGISTRY_EXTENSION_MANAGER.enable(namespace, name)
  except RegistryExtensionError as error:
    _raise_registry_http_error(error)


@REGISTRY_ROUTER.post("/{namespace}/{name}/disable")
async def disable_registry_extension(
  namespace: str,
  name: str,
) -> ExtensionInstallationModel:
  try:
    return await REGISTRY_EXTENSION_MANAGER.disable(namespace, name)
  except RegistryExtensionError as error:
    _raise_registry_http_error(error)
