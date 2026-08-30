"""Run API Service."""

import asyncio
import contextlib
import os

import fastapi
import uvicorn
from fastapi.responses import JSONResponse

# Setup logging
from libs.obsrv.main import setup_obsrv

logger = setup_obsrv()
# Setup logging end

# Load flags
SKIP_EXTENSION_START: bool = os.getenv("SKIP_EXTENSION_START", "").lower() in (
  "1",
  "true",
  "yes",
)
# Load flags end

from fastapi.middleware.cors import CORSMiddleware
from app.settings import settings
from app.routes.block import ROUTER as block_router
from app.routes.relation import ROUTER as relation_router
from app.routes.extension import PEER_INBOUND as extension_peer_inbound
from app.routes.extension import ROUTER as extension_router
from app.routes.source import ROUTER as source_router
from app.routes.deployment_config import ROUTER as deployment_config_router
from app.routes.info_base import ROUTER as info_base_router
from app.routes.lexical_retrieval import PEER_INBOUND as lexical_retrieval_peer_inbound
from app.routes.lexical_retrieval import ROUTER as lexical_retrieval_router
from app.routes.organization import PEER_INBOUND as organization_peer_inbound
from app.routes.organization import ROUTER as organization_router
from app.routes.semantic_retrieval import PEER_INBOUND as semantic_retrieval_peer_inbound
from app.routes.semantic_retrieval import ROUTER as semantic_retrieval_router
from app.routes.sink import ROUTER as sink_router
from app.business.source import SourceManager
from app.business.cron import CronManager
from app.business.job import JobManager
from app.business.extension import EXTENSION_HOST
from app.business.peer import PeerManager
from app.business.ai import AIManager
from app.business.sink import SinkManager

# Import core-owned Job contracts before their catalog is synchronized.
from app.business.organization_job import MediaInterpretationJobHandler  # noqa: F401
from app.middleware import LoggingMiddleware, require_peer_jwt
from app.schemas.peer import PEER_EXECUTION_HEADER
from app.health import check_database_readiness
from app.runtime import RUNTIME_STATUS, RuntimePhase


# Import scheduler
from app.scheduler import scheduler


async def bootstrap_runtime(app: fastapi.FastAPI) -> None:
  """Initialize database-backed runtime services after migrations are ready."""
  from app.business.info_base.resolver import register_core_resolvers
  from app.business.info_base.storage import StorageManager

  # Register this Peer first so extension enablement can resolve its identity.
  PeerManager.register_self()
  PeerManager.setup_builtin_outbounds()
  PeerManager.register_inbound(semantic_retrieval_peer_inbound)
  PeerManager.register_inbound(lexical_retrieval_peer_inbound)
  PeerManager.register_inbound(organization_peer_inbound)
  PeerManager.register_inbound(extension_peer_inbound)

  # Core decoders exist independently of installed/enabled extensions.
  register_core_resolvers()

  # Setup built-in storage instances
  StorageManager.setup_builtin_storages()

  if not SKIP_EXTENSION_START:
    await EXTENSION_HOST.start_enabled(app)
  SourceManager.sync_source_types()

  # Extensions may register Sink types, but persisted instances run only by intent.
  await SinkManager.startup(app, PeerManager.get_current_peer_ref())

  JobManager.sync_job_types()

  AIManager.sync_dialects()

  # Publish only after every provider route and runtime-owned capability is ready.
  PeerManager.refresh_self(settings.peer_lease_ttl_seconds)

  if not scheduler.running:
    scheduler.start()

  # Peer-local timers only wake the database-owned Cron and Job lifecycles.
  scheduler.add_job(
    PeerManager.refresh_self,
    "interval",
    seconds=settings.peer_lease_renew_interval_seconds,
    args=[settings.peer_lease_ttl_seconds],
    id="peer.refresh_self",
    replace_existing=True,
  )
  scheduler.add_job(
    JobManager.check,
    "interval",
    seconds=30,
    id="jobs.check",
    replace_existing=True,
  )
  scheduler.add_job(
    CronManager.check,
    "interval",
    seconds=30,
    id="crons.check",
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
    await bootstrap_runtime(app)
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
  runtime_was_ready = RUNTIME_STATUS.ready
  RUNTIME_STATUS.set(RuntimePhase.STOPPING, "application_shutdown")
  bootstrap_task.cancel()
  with contextlib.suppress(asyncio.CancelledError):
    await bootstrap_task
  if scheduler.running:
    scheduler.shutdown(wait=True)
  await SinkManager.shutdown()
  await EXTENSION_HOST.close_running()
  if runtime_was_ready:
    await asyncio.to_thread(PeerManager.clear_self_lease)


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
  expose_headers=[PEER_EXECUTION_HEADER],
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


core_router = fastapi.APIRouter(
  dependencies=[fastapi.Depends(require_peer_jwt)],
)

core_router.include_router(block_router)
core_router.include_router(relation_router)
core_router.include_router(extension_router)
core_router.include_router(source_router)
core_router.include_router(deployment_config_router)
core_router.include_router(info_base_router)
core_router.include_router(organization_router)
core_router.include_router(semantic_retrieval_router)
core_router.include_router(lexical_retrieval_router)
core_router.include_router(sink_router)
api_app.include_router(core_router)

if __name__ == "__main__":
  uvicorn.run(api_app, host=settings.host, port=settings.port)
