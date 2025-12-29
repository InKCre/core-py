"""Run API Service."""

import sys
import os
import contextlib
import fastapi
import uvicorn

# Setup logging
from libs.obsrv.main import setup_obsrv

logger = setup_obsrv()
# Setup logging end

# Load flags
SKIP_EXTENSIONS_SYNC: bool = os.getenv("SKIP_EXTENSIONS_SYNC", "").lower() in (
  "1",
  "true",
  "yes",
)
# Load flags end

sys.path.insert(0, "extensions")

from fastapi.middleware.cors import CORSMiddleware
from app.settings import settings
from app.routes.block import ROUTER as block_router
from app.routes.relation import ROUTER as relation_router
from app.routes.extension import ROUTER as extension_router
from app.routes.source import ROUTER as source_router
from app.business.source import SourceManager
from app.business.extension import ExtensionManager
from app.business.info_base.main import InfoBaseManager
from app.business.sink import SinkManager
from app.middleware import LoggingMiddleware, JWTMiddleware


# Import scheduler
from app.scheduler import scheduler


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
  from app.business.source import SourceCollectJobManager
  from app.business.info_base.storage import StorageManager
  from app.business.sink.embedding import EmbeddingManager

  logger.info("Application startup")

  # Setup built-in storage instances
  StorageManager.setup_builtin_storages()

  scheduler.start()

  # Add periodic job to check pending source collect jobs
  scheduler.add_job(
    SourceCollectJobManager.check,
    "interval",
    seconds=30,
    id="sources.collect_jobs.check_pending",
  )

  # Add periodic job to check and create missing embeddings
  scheduler.add_job(
    EmbeddingManager.check_and_create_missing_embeddings,
    "interval",
    seconds=60,  # Check every minute
    id="sink.embeddings.check_missing",
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

root_router.put("/graph")(InfoBaseManager.insert_subgrpah)
sink_router.get("/rag")(SinkManager.rag)

api_app.include_router(block_router)
api_app.include_router(relation_router)
api_app.include_router(extension_router)
api_app.include_router(source_router)
api_app.include_router(root_router)
api_app.include_router(sink_router)

# must be prior
# Skip extension sync if SKIP_EXTENSIONS_SYNC is set (useful for OpenAPI generation)
if not SKIP_EXTENSIONS_SYNC:
  ExtensionManager.sync()
  ExtensionManager.start_enabled(api_app)
  SourceManager.set_up_collect_jobs()


if __name__ == "__main__":
  uvicorn.run(api_app, host=settings.host, port=settings.port)
