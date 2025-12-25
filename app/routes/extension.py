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
  return ExtensionManager.get_installed(disabled=None)


@ROUTER.post("/{extid}")
def install_extension(
  extid: ExtensionID,
  disabled: bool = fastapi.Query(default=False),
  version: str | None = fastapi.Query(default=None),
) -> ExtensionModel:
  """安装插件 (Install extension)"""
  return ExtensionManager.install(extid, version=version)


@ROUTER.put("/{extid}/disabled/{disabled}")
async def toggle_extension(extid: ExtensionID, disabled: bool) -> ExtensionModel:
  """启用/禁用插件 (Enable/Disable extension)"""
  try:
    return await ExtensionManager.set_disabled(extid, disabled)
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
