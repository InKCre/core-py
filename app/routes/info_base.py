"""Info-base graph command HTTP resource."""

__all__ = ["ROUTER"]

import fastapi

from app.business.info_base.main import InfoBaseManager
from app.schemas.info_base.main import GraphForm, SubmitGraphResult


ROUTER = fastapi.APIRouter(tags=["info-base"])


@ROUTER.put("/graph")
def submit_graph(body: GraphForm) -> SubmitGraphResult:
  return InfoBaseManager.submit_graph(body)
