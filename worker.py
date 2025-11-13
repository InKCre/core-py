"""Cloudflare Worker entry point for InKCre Core.

This module provides an ASGI application compatible with Cloudflare Workers.
It wraps the FastAPI application and handles the differences between
traditional deployment and Cloudflare Workers environment.
"""

import contextlib
import os
import typing
import fastapi
from fastapi.middleware.cors import CORSMiddleware
from app.routes.block import ROUTER as block_router
from app.routes.relation import ROUTER as relation_router
from app.business.source import SourceManager
from app.business.extension import ExtensionManager
from app.business.root import RootManager
from app.business.sink import SinkManager


# Detect if running in Cloudflare Workers environment
IS_CLOUDFLARE_WORKER = os.getenv("CF_WORKER", "false").lower() == "true"


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    """Application lifespan handler.
    
    Note: APScheduler is disabled in Cloudflare Workers environment
    as background tasks are not supported. Use Cloudflare Cron Triggers instead.
    """
    if not IS_CLOUDFLARE_WORKER:
        # Only start scheduler in traditional deployment
        from app.task import scheduler
        scheduler.start()
    
    yield
    
    if not IS_CLOUDFLARE_WORKER:
        from app.task import scheduler
        scheduler.shutdown(wait=True)
    
    await ExtensionManager.close_all()


# Create FastAPI application
app = fastapi.FastAPI(title="InKCre", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up routes
app.get("/heartbeat")(lambda: {"status": "ok", "worker": IS_CLOUDFLARE_WORKER})

source_router = fastapi.APIRouter(prefix="/source", tags=["sources"])
root_router = fastapi.APIRouter(tags=["root"])
sink_router = fastapi.APIRouter(prefix="/sink", tags=["sink"])

source_router.get("/{source_id}/collect")(SourceManager.run_a_collect)
root_router.put("/graph")(RootManager.insert_grpah)
sink_router.get("/rag")(SinkManager.rag)

app.include_router(block_router)
app.include_router(relation_router)
app.include_router(source_router)
app.include_router(root_router)
app.include_router(sink_router)

# Set up collect jobs only in non-Worker environment
# In Workers, use Cloudflare Cron Triggers to call /source/{source_id}/collect
if not IS_CLOUDFLARE_WORKER:
    SourceManager.set_up_collect_jobs()

# Start extensions
ExtensionManager.start_all(app)

# Export for Cloudflare Workers
# The 'app' variable is the ASGI application that Workers will use
