"""Run API Service."""

import sys

sys.path.insert(0, "extensions")

import contextlib
import fastapi
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from app.settings import settings
from app.routes.block import ROUTER as block_router
from app.routes.relation import ROUTER as relation_router
from app.routes.extension import ROUTER as extension_router
from app.routes.source import ROUTER as source_router
from app.business.source import SourceManager
from app.business.extension import ExtensionManager
from app.business.root import RootManager
from app.business.sink import SinkManager
from app.logging_config import setup_logging
from app.middleware import LoggingMiddleware, JWTMiddleware

# Setup logging
logger = setup_logging()

# Import scheduler
from app.scheduler import scheduler


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    from app.business.source import SourceCollectJobManager

    logger.info("Application startup")
    scheduler.start()

    # Add periodic job to check pending source collect jobs
    scheduler.add_job(
        SourceCollectJobManager.check_pending,
        "interval",
        seconds=30,
        id="sources.collect_jobs.check_pending",
    )

    yield
    logger.info("Application shutdown")
    scheduler.shutdown(wait=True)
    await ExtensionManager.close_running()


api_app = fastapi.FastAPI(title="InKCre", lifespan=lifespan)

# 添加日志中间件
api_app.add_middleware(LoggingMiddleware)

# 添加JWT认证中间件
api_app.add_middleware(JWTMiddleware)

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

root_router = fastapi.APIRouter(tags=["root"])
sink_router = fastapi.APIRouter(prefix="/sink", tags=["sink"])

root_router.put("/graph")(RootManager.insert_grpah)
sink_router.get("/rag")(SinkManager.rag)

api_app.include_router(block_router)
api_app.include_router(relation_router)
api_app.include_router(extension_router)
api_app.include_router(source_router)
api_app.include_router(root_router)
api_app.include_router(sink_router)

# must be prior
ExtensionManager.sync()
ExtensionManager.start_enabled(api_app)

SourceManager.set_up_collect_jobs()


if __name__ == "__main__":
    uvicorn.run(api_app, host=settings.host, port=settings.port)
