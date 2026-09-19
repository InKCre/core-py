"""Isolated PostgreSQL log ownership and scheduler cancellation acceptance."""

import asyncio
import logging
import uuid

import sqlalchemy
import sqlmodel

from app.engine import ASYNC_DB_ENGINE, AsyncSessionFactory
from app.persistence.info_base.uow import graph_uow
from app.scheduler import drain_scheduler, scheduler, start_scheduler, with_trace_id
from app.schemas.info_base.block import BlockForm
from libs.obsrv.log_handler_postgresql import PostgreSQLHandler
from libs.obsrv.log_record import ENABLE_LOG_BACKEND, TRACE_ID, LogModel


async def main():
  marker = uuid.uuid4().hex
  handler = PostgreSQLHandler(logging.INFO)
  handler.start()
  token = ENABLE_LOG_BACKEND.set(True)
  trace = TRACE_ID.set(marker)

  def emit():
    handler.handle(logging.LogRecord("probe", logging.INFO, __file__, 1, marker, (), None))

  try:
    try:
      async with graph_uow() as uow:
        await uow.blocks.create(BlockForm(resolver="core.text.v1", content=marker))
        emit()
        await asyncio.to_thread(emit)
        raise ValueError("rollback application operation")
    except ValueError:
      pass
    await handler.aclose()
    async with AsyncSessionFactory.begin() as session:
      records = tuple(
        await session.scalars(sqlmodel.select(LogModel).where(LogModel.body == marker))
      )
      assert len(records) == 2 and all(record.trace_id == marker for record in records)
      await session.execute(sqlalchemy.delete(LogModel).where(LogModel.body == marker))
    async with graph_uow() as uow:
      assert await uow.blocks.matching_content("core.text.v1", marker) == ()

    started = asyncio.Event()
    cleaned = asyncio.Event()

    async def callback():
      try:
        started.set()
        await asyncio.Event().wait()
      finally:
        await asyncio.sleep(0.01)
        cleaned.set()

    start_scheduler()
    task = asyncio.create_task(with_trace_id(marker, callback)())
    await started.wait()
    await drain_scheduler()
    assert task.done() and cleaned.is_set()
    scheduler.shutdown()
    await asyncio.sleep(0)
    print("log isolation, thread context, shutdown drain: passed")
  finally:
    ENABLE_LOG_BACKEND.reset(token)
    TRACE_ID.reset(trace)
    await handler.aclose()
    await ASYNC_DB_ENGINE.dispose()


if __name__ == "__main__":
  asyncio.run(main())
