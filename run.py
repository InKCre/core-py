"""Run API Service."""

import asyncio
import contextlib
import fastapi
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware
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
    from app.pgsql_listen import listen_for_pgsql
    from app.business.source import SourceCollectJobManager

    logger.info("Application startup")
    scheduler.start()

    database_scale_0 = os.getenv("DATABASE_SCALE_0", "false").lower() == "true"

    # Start the job listener task
    listener_task = None
    if not database_scale_0:
        listener_task = asyncio.create_task(
            listen_for_pgsql({"job_created": SourceCollectJobManager.handle_created})
        )

    yield
    logger.info("Application shutdown")
    scheduler.shutdown(wait=True)
    if listener_task:
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
    await ExtensionManager.close_all()


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
ExtensionManager.start_all(api_app)

SourceManager.set_up_collect_jobs()


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(api_app, host=host, port=port)
