"""Fixed semantic-retrieval HTTP inbound."""

__all__ = ["ROUTER"]

import fastapi

from app.business.peer import PeerHTTPInbound
from app.business.semantic_retrieval import (
  SEMANTIC_RETRIEVAL_CAPABILITY,
  SemanticRetrievalManager,
)
from app.schemas.semantic_retrieval import (
  SemanticRetrievalRequest,
  SemanticRetrievalResult,
)


ROUTER = fastapi.APIRouter(tags=["semantic-retrieval"])
PEER_INBOUND = PeerHTTPInbound(
  capability=SEMANTIC_RETRIEVAL_CAPABILITY,
  method="POST",
  path="/semantic-retrieval",
)


@ROUTER.post("/semantic-retrieval")
async def retrieve(body: SemanticRetrievalRequest) -> SemanticRetrievalResult:
  return await SemanticRetrievalManager.retrieve_local(
    body.query,
    body.profile,
    body.options,
  )
