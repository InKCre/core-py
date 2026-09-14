"""Info-base graph command HTTP resource."""

__all__ = ["ROUTER"]

import fastapi

from app.business.info_base.main import InfoBaseManager
from app.schemas.info_base.main import GraphForm, SubmitGraphResult
from .validation import database_write


ROUTER = fastapi.APIRouter(tags=["info-base"])


@ROUTER.post("/graph")
def submit_graph(body: GraphForm) -> SubmitGraphResult:
  with database_write():
    return InfoBaseManager.submit_graph(body)
