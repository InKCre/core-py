"""Run API Service."""

import asyncio
import contextlib
import os
import sys

import fastapi
import uvicorn
from fastapi.responses import JSONResponse

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
from app.business.client import ClientManager
from app.business.info_base.main import InfoBaseManager
from app.business.sink import SinkManager
from app.middleware import LoggingMiddleware, require_peer_jwt
from app.health import check_database_readiness
from app.runtime import RUNTIME_STATUS, RuntimePhase


# Import scheduler
from app.scheduler import scheduler


def bootstrap_runtime(app: fastapi.FastAPI) -> None:
  """Initialize database-backed runtime services after migrations are ready."""
  from app.business.source import SourceCollectJobManager
  from app.business.info_base.storage import StorageManager
  from app.business.sink.embedding import EmbeddingManager

  # Register this client first
  ClientManager.register_self()

  # Setup built-in storage instances
  StorageManager.setup_builtin_storages()

  if not SKIP_EXTENSIONS_SYNC:
    ExtensionManager.sync()
    ExtensionManager.load_installed_decoders()
    ExtensionManager.start_enabled(app)
    SourceManager.sync_source_types()
    SourceManager.set_up_collect_jobs()

  if not scheduler.running:
    scheduler.start()

  # Add periodic job to check pending source collect jobs
  scheduler.add_job(
    SourceCollectJobManager.check,
    "interval",
    seconds=30,
    id="sources.collect_jobs.check_pending",
    replace_existing=True,
  )

  # Add periodic job to check and create missing embeddings
  scheduler.add_job(
    EmbeddingManager.check_and_create_missing_embeddings,
    "interval",
    seconds=60,  # Check every minute
    id="sink.embeddings.check_missing",
    replace_existing=True,
  )


async def bootstrap_when_database_is_ready(app: fastapi.FastAPI) -> None:
  """Wait for a migrated database, then initialize the runtime once."""
  retry_seconds = float(os.getenv("RUNTIME_BOOTSTRAP_RETRY_SECONDS", "5"))

  while True:
    database = await asyncio.to_thread(check_database_readiness)
    if database.ready:
      break
    RUNTIME_STATUS.set(RuntimePhase.WAITING_FOR_DATABASE, database.reason)
    await asyncio.sleep(retry_seconds)

  try:
    bootstrap_runtime(app)
  except Exception:
    RUNTIME_STATUS.set(RuntimePhase.FAILED, "runtime_bootstrap_failed")
    logger.exception("Runtime bootstrap failed")
    return

  RUNTIME_STATUS.set(RuntimePhase.READY, "ready")
  logger.info("Runtime bootstrap completed")


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
  logger.info("Application startup")
  RUNTIME_STATUS.set(RuntimePhase.STARTING, "runtime_bootstrap_pending")
  bootstrap_task = asyncio.create_task(bootstrap_when_database_is_ready(app))

  yield

  logger.info("Application shutdown")
  RUNTIME_STATUS.set(RuntimePhase.STOPPING, "application_shutdown")
  bootstrap_task.cancel()
  with contextlib.suppress(asyncio.CancelledError):
    await bootstrap_task
  if scheduler.running:
    scheduler.shutdown(wait=True)
  await ExtensionManager.close_running()


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
@api_app.get("/livez")
def liveness() -> dict[str, str]:
  """Report process liveness without checking dependencies."""
  return {"status": "ok"}


api_app.get("/heartbeat", include_in_schema=False)(liveness)


@api_app.get("/readyz")
async def readiness() -> JSONResponse:
  """Report database and runtime compatibility without mutating either."""
  database = await asyncio.to_thread(check_database_readiness)
  runtime = RUNTIME_STATUS.as_dict()
  ready = database.ready and RUNTIME_STATUS.ready
  return JSONResponse(
    status_code=200 if ready else 503,
    content={
      "status": "ready" if ready else "not_ready",
      "database": database.as_dict(),
      "runtime": runtime,
    },
  )


root_router = fastapi.APIRouter(tags=["root"])
sink_router = fastapi.APIRouter(prefix="/sink", tags=["sink"])
core_router = fastapi.APIRouter(
  dependencies=[fastapi.Depends(require_peer_jwt)],
)

root_router.put("/graph")(InfoBaseManager.insert_subgrpah)
sink_router.get("/rag")(SinkManager.rag)

core_router.include_router(block_router)
core_router.include_router(relation_router)
core_router.include_router(extension_router)
core_router.include_router(source_router)
core_router.include_router(root_router)
core_router.include_router(sink_router)
api_app.include_router(core_router)

if __name__ == "__main__":
  uvicorn.run(api_app, host=settings.host, port=settings.port)
