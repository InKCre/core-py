"""Memos-owned connection address for admitted deployment Peers."""

import fastapi
import pydantic

from app.business.peer import PeerHTTPInbound
from app.http import get_public_http_base_url
from app.middleware import require_peer_jwt


MEMOS_CONNECTION_INBOUND = PeerHTTPInbound(
  "memos.connection.v1", "GET", "/memos/connection"
)


class MemosConnection(pydantic.BaseModel):
  server_url: str


def register_connection_route(router: fastapi.APIRouter) -> None:
  @router.get("/connection", dependencies=[fastapi.Depends(require_peer_jwt)])
  async def connection() -> MemosConnection:
    base = await get_public_http_base_url()
    if base is None:
      raise fastapi.HTTPException(
        status_code=409,
        detail="Configure this Core's Public HTTP Base URL before connecting Memos.",
      )
    return MemosConnection(server_url=f"{base}/memos")
