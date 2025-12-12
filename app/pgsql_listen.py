import asyncio
import logging
from typing import Callable, Awaitable
import psycopg
import psycopg.sql
from app.engine import DATABASE_URL

logger = logging.getLogger(__name__)


async def listen_for_pgsql(event_handlers: dict[str, Callable[[str], Awaitable[None]]]):
    """Listen for PostgreSQL notifications and handle events."""

    # TODO add pool_ping or other solution to avoid dead connection
    async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            for event_name in event_handlers:
                query = psycopg.sql.SQL("LISTEN {}").format(
                    psycopg.sql.Identifier(event_name)
                )
                await cur.execute(query)
                logger.info(f"Listening for '{event_name}' notifications")

            while True:
                try:
                    async for notify in conn.notifies():
                        logger.info(f"Received notification: {notify.payload}")
                        handler = event_handlers.get(notify.channel)
                        if handler:
                            await handler(notify.payload)
                        else:
                            logger.warning(f"No handler for event '{notify.channel}'")
                except Exception as e:
                    logger.error(f"Error in notification listener: {e}")
                    await asyncio.sleep(1)  # Wait before retrying
