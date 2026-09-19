"""Log batches commit independently of application transactions."""

from collections.abc import Sequence

from app.engine import AsyncSessionFactory
from libs.obsrv.log_record import LogModel


async def write_logs(entries: Sequence[LogModel]) -> None:
  async with AsyncSessionFactory.begin() as session:
    session.add_all(entries)
