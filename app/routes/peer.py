"""Peer record/lease observation; no capability invocation or wake protocol."""

import typing

import fastapi

from app.business.peer import PeerManager
from app.schemas.peer import PeerRef


ROUTER = fastapi.APIRouter(prefix="/peers", tags=["peer"])


@ROUTER.get("")
def list_peers(
  limit: int | None = fastapi.Query(None, gt=0), cursor: PeerRef | None = None
) -> dict[str, typing.Any]:
  peers, next_cursor = PeerManager.list_with_leases(limit=limit, cursor=cursor)
  return {"peers": peers, "next_cursor": next_cursor}


@ROUTER.get("/self")
def get_self_peer() -> dict:
  return get_peer(PeerManager.get_current_peer_ref())


@ROUTER.get("/{peer_id}")
def get_peer(peer_id: PeerRef) -> dict:
  result = PeerManager.get_with_lease(peer_id)
  if result is None:
    raise fastapi.HTTPException(404, f"Peer {peer_id} not found")
  return result
