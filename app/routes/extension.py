"""Extension Module's API Endpoints"""

__all__ = ["ROUTER"]

import fastapi
import sqlmodel
from app.schemas.extension import ExtensionModel, ExtensionID
from app.engine import SessionLocal

ROUTER = fastapi.APIRouter(
    prefix="/extensions",
    tags=["extension", "插件"],
)


@ROUTER.post("/{extension_id}")
def install_extension(extension_id: ExtensionID) -> ExtensionModel:
    """安装插件 (Install extension)"""
    with SessionLocal() as db:
        # Check if extension already exists
        existing = db.exec(
            sqlmodel.select(ExtensionModel).where(ExtensionModel.id == extension_id)
        ).first()
        
        if existing:
            # If already installed, return the existing extension
            return existing
        
        # Create new extension record
        # Default version format as shown in the spec: (0,1,0)
        extension = ExtensionModel(
            id=extension_id,
            version="(0,1,0)",
            disabled=False,
            nickname=extension_id,  # Use id as default nickname
            config={},
            state={}
        )
        
        db.add(extension)
        db.commit()
        db.refresh(extension)
        
        return extension


@ROUTER.put("/{extension_id}/config")
def update_extension_config(
    extension_id: ExtensionID,
    config: dict
) -> dict:
    """编辑插件配置 (Edit extension configuration)"""
    from app.business.extension import ExtensionManager
    
    updated_config = ExtensionManager.update_config(extension_id, config)
    
    if updated_config is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"Extension with id {extension_id} not found."
        )
    
    return updated_config or {}
