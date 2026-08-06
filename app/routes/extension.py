"""Extension Module's API Endpoints"""

__all__ = ["ROUTER"]

import fastapi
import pydantic
from app.business.extension import EXTENSION_MANAGEMENT_CAPABILITY, ExtensionManager
from app.business.peer import PeerHTTPInbound
from app.schemas.extension import (
  ExtensionID,
  ExtensionManagementCommand,
  ExtensionModel,
)

ROUTER = fastapi.APIRouter(
  tags=["extension"],
)
PEER_INBOUND = PeerHTTPInbound(
  capability=EXTENSION_MANAGEMENT_CAPABILITY,
  method="POST",
  path="/extension-management",
)


@ROUTER.get("/extensions")
def get_extensions() -> tuple[ExtensionModel, ...]:
  """List all installed extensions"""
  return ExtensionManager.get_installed()


@ROUTER.post("/extensions/{extid}")
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


@ROUTER.post("/extension-management")
async def manage_extension(
  body: ExtensionManagementCommand,
) -> ExtensionModel:
  """Execute one fixed, Peer-local Extension management command."""
  try:
    return await ExtensionManager.manage_local(body)
  except pydantic.ValidationError as error:
    raise fastapi.HTTPException(
      status_code=fastapi.status.HTTP_422_UNPROCESSABLE_CONTENT,
      detail=error.errors(),
    ) from error
  except ValueError as error:
    raise fastapi.HTTPException(
      status_code=fastapi.status.HTTP_404_NOT_FOUND,
      detail=str(error),
    ) from error
