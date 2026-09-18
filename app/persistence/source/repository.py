"""Persistence for Source catalog and instances."""

import sqlmodel
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.source import SourceModel, SourceTypesModel


class SourceRepository:
  def __init__(self, session: AsyncSession) -> None:
    self._session = session

  async def sync_types(self, rows: list[dict]) -> None:
    if not rows:
      return
    statement = insert(SourceTypesModel).values(rows)
    statement = statement.on_conflict_do_update(
      index_elements=[SourceTypesModel.id],
      set_={
        key: getattr(statement.excluded, key)
        for key in (
          "description",
          "config_schema",
          "collect_config_schema",
          "backfill_config_schema",
        )
      },
    )
    await self._session.execute(statement)

  async def get(self, source_id: int, *, lock: bool = False):
    statement = sqlmodel.select(SourceModel).where(SourceModel.id == source_id)
    if lock:
      statement = statement.with_for_update()
    return (await self._session.scalars(statement)).one_or_none()

  async def save(self, source: SourceModel) -> None:
    self._session.add(source)
    await self._session.flush()
    await self._session.refresh(source)
