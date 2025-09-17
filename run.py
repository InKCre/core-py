"""Run API Service."""

import contextlib
import typing
import fastapi
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from app.routes.block import ROUTER as block_router
from app.routes.relation import ROUTER as relation_router


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    from app.task import scheduler
    scheduler.start()
    yield
    scheduler.shutdown(wait=True)
    await ExtensionManager.close_all()


api_app = fastapi.FastAPI(title="InKCre", lifespan=lifespan)

# 添加CORS中间件以支持跨域请求
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置为具体的域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)


# Set up routes
api_app.get("/heartbeat")(lambda: {"status": "ok"})

from app.business.source import SourceManager  # noqa: E402
source_router = fastapi.APIRouter(prefix="/source", tags=["sources"])
source_router.get("/{source_id}/collect")(SourceManager.run_a_collect)
api_app.include_router(block_router)
api_app.include_router(relation_router)
api_app.include_router(source_router)
SourceManager.set_up_collect_jobs()


if __name__ == "__main__":
    uvicorn.run(api_app, host="0.0.0.0", port=8000)
