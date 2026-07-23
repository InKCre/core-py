"""Extension Module's API Endpoints"""

__all__ = ["ROUTER"]

import typing
import fastapi
from app.business.extension.main import ExtensionManager
from app.schemas.extension.main import ExtensionModel, ExtensionID

ROUTER = fastapi.APIRouter(
  prefix="/extensions",
  tags=["extension"],
)


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
