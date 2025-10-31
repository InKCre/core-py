"""Run API Service."""

import contextlib
import fastapi
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from app.routes.block import ROUTER as block_router
from app.routes.relation import ROUTER as relation_router
from app.routes.extension import ROUTER as extension_router
from app.business.source import SourceManager
from app.business.extension import ExtensionManager
from app.business.root import RootManager
from app.business.sink import SinkManager
from app.logging_config import setup_logging
from app.middleware import LoggingMiddleware

# Setup logging
logger = setup_logging()


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    from app.task import scheduler

    logger.info("Application startup")
    scheduler.start()
    yield
    logger.info("Application shutdown")
    scheduler.shutdown(wait=True)
    await ExtensionManager.close_all()


api_app = fastapi.FastAPI(title="InKCre", lifespan=lifespan)

# 添加日志中间件
api_app.add_middleware(LoggingMiddleware)

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

source_router = fastapi.APIRouter(prefix="/source", tags=["sources"])
root_router = fastapi.APIRouter(tags=["root"])
sink_router = fastapi.APIRouter(prefix="/sink", tags=["sink"])

source_router.get("/{source_id}/collect")(
    SourceManager.run_a_collect
)  # TODO move to business/source.py
root_router.put("/graph")(RootManager.insert_grpah)
sink_router.get("/rag")(SinkManager.rag)

api_app.include_router(block_router)
api_app.include_router(relation_router)
api_app.include_router(extension_router)
api_app.include_router(source_router)
api_app.include_router(root_router)
api_app.include_router(sink_router)


SourceManager.set_up_collect_jobs()

ExtensionManager.start_all(api_app)


if __name__ == "__main__":
    uvicorn.run(api_app, host="0.0.0.0", port=8000)
