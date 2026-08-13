"""Fixed local organization rumination HTTP inbound."""

__all__ = ["ROUTER"]

import fastapi

from app.business.organization import RUMINATION_CAPABILITY, OrganizationManager
from app.business.peer import PeerHTTPInbound
from app.schemas.organization import RuminationRequest


ROUTER = fastapi.APIRouter(tags=["organization"])
PEER_INBOUND = PeerHTTPInbound(
  capability=RUMINATION_CAPABILITY,
  method="POST",
  path="/organization/ruminate",
)


@ROUTER.post(
  "/organization/ruminate",
  status_code=fastapi.status.HTTP_204_NO_CONTENT,
)
async def ruminate(body: RuminationRequest) -> None:
  await OrganizationManager.ruminate_local(body.block)
