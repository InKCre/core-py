"""Fixed lexical-retrieval HTTP inbound."""

__all__ = ["PEER_INBOUND", "ROUTER"]

import fastapi

from app.business.lexical_retrieval import (
  LEXICAL_RETRIEVAL_CAPABILITY,
  LexicalRetrievalManager,
)
from app.business.peer import PeerHTTPInbound
from app.schemas.lexical_retrieval import (
  LexicalRetrievalRequest,
  LexicalRetrievalResult,
)


ROUTER = fastapi.APIRouter(tags=["lexical-retrieval"])
PEER_INBOUND = PeerHTTPInbound(
  capability=LEXICAL_RETRIEVAL_CAPABILITY,
  method="POST",
  path="/lexical-retrieval",
)


@ROUTER.post("/lexical-retrieval")
async def retrieve(body: LexicalRetrievalRequest) -> LexicalRetrievalResult:
  return LexicalRetrievalManager.retrieve_local(body.query, body.limit)
