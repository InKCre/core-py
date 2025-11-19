"""Extension Module's API Endpoints"""

__all__ = ["ROUTER"]

import fastapi
from app.business.extension import ExtensionManager
from app.schemas.extension import ExtensionModel, ExtensionID

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
def enable_extension(extid: ExtensionID, disabled: bool) -> ExtensionModel:
    """启用/禁用插件 (Enable/Disable extension)"""
    try:
        return ExtensionManager.set_disabled(extid, disabled)
    except ValueError:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"Extension with id {extid} not found.",
        )


@ROUTER.put("/{extid}/config")
def update_extension_config(extid: ExtensionID, config: dict) -> ExtensionModel:
    """编辑插件配置 (Edit extension configuration)"""
    updated = ExtensionManager.save_config_and_state(extid, config)

    if updated is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"Extension with id {extid} not found.",
        )

    return updated
