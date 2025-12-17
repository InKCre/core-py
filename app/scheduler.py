__all__ = ["scheduler", "with_trace_id"]

import apscheduler.schedulers.asyncio

from libs.obsrv.log_record import ENABLE_LOG_BACKEND, TRACE_ID

scheduler = apscheduler.schedulers.asyncio.AsyncIOScheduler()


def with_trace_id(trace_id: str, coro, enable_backend: bool = True):
    async def wrapper(*args, **kwargs):
        token = TRACE_ID.set(trace_id)
        token_backend = ENABLE_LOG_BACKEND.set(enable_backend)
        try:
            return await coro(*args, **kwargs)
        finally:
            TRACE_ID.reset(token)
            ENABLE_LOG_BACKEND.reset(token_backend)

    return wrapper
