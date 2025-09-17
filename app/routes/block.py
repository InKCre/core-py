"""Block Module's API Enpoints"""

__all__ = ["ROUTER"]

import fastapi
import typing
from app.business.block import BlockManager, BlockModel

ROUTER = fastapi.APIRouter(
    prefix="/blocks",
    tags=["block"],
)


ROUTER.get("/recent")(BlockManager.get_recent)


@ROUTER.get("/{block_id}")
def get_block_by_id(block_id: int) -> BlockModel:
    block = BlockManager.get(block_id)
    if block is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"Block with id {block_id} not found.",
        )
    return block


@ROUTER.post("")
def create_block(
    body: BlockModel,
    response: fastapi.Response,
    background_tasks: fastapi.BackgroundTasks,
    organize: bool = True,
) -> BlockModel:
    """创建块"""
    body = BlockManager.create(body)

    if organize:
        background_tasks.add_task(BlockManager.organize, body)

    response.status_code = 201
    return body


@ROUTER.get("/by_embedding")
def query_by_embedding(
    block_id: int,
    num: int = 10,
) -> tuple[BlockModel, ...]:
    return BlockManager.query_by_embedding(
        block_id=block_id,
        num=num,
    )


@ROUTER.patch("/{block_id}")
def edit_block(
    block_id: int,
    body: BlockModel,
    background_tasks: fastapi.BackgroundTasks,
    organize: bool = False,
) -> BlockModel:
    """编辑块（部分更新），只更新请求中提供的字段。"""
    try:
        updated = BlockManager.edit_block(block_id, body)
    except ValueError:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"Block with id {block_id} not found.",
        )
    else:
        if organize:
            background_tasks.add_task(BlockManager.organize, updated)

        return updated
