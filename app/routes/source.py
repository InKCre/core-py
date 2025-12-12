"""Source Module's API Endpoints"""

__all__ = ["ROUTER"]

import fastapi
import typing
from app.business.source import SourceManager
from app.schemas.block import BlockModel

ROUTER = fastapi.APIRouter(
    prefix="/sources",
    tags=["source"],
)


@ROUTER.post("/{source_id}/collect")
async def collect_source(source_id: int, full: bool = False) -> list[BlockModel]:
    """Create a source collect job."""
    # TODO
    return await SourceManager.run_a_collect(source_id, full)
