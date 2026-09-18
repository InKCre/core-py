"""Session-bound access to canonical Extension rows and the enabled RPC."""

import uuid

import sqlalchemy
import sqlmodel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_contract.constants import PROTOCOL_SCHEMA
from app.schemas.extension import ExtensionModel


class ExtensionRepository:
  def __init__(self, session: AsyncSession) -> None:
    self._session = session

  async def list(self):
    rows = await self._session.scalars(
      sqlmodel.select(ExtensionModel).order_by(ExtensionModel.name)
    )
    return tuple(rows)

  async def get(self, name: str, *, lock: bool = False):
    statement = sqlmodel.select(ExtensionModel).where(ExtensionModel.name == name)
    if lock:
      statement = statement.with_for_update()
    return (await self._session.scalars(statement)).one_or_none()

  async def try_install_lock(self, name: str) -> bool:
    result = await self._session.execute(
      sqlalchemy.text("SELECT pg_try_advisory_xact_lock(hashtextextended(:name, 0))"),
      {"name": name},
    )
    return bool(result.scalar_one())

  async def save(self, row: ExtensionModel) -> None:
    self._session.add(row)
    await self._session.flush()

  async def delete(self, row: ExtensionModel) -> None:
    await self._session.delete(row)

  async def set_peer_enabled(self, name: str, peer_id: uuid.UUID, enabled: bool):
    result = await self._session.execute(
      sqlalchemy.text(
        f"SELECT * FROM {PROTOCOL_SCHEMA}.set_extension_peer_enabled("
        ":p_name, :p_peer_id, :p_enabled)"
      ),
      {"p_name": name, "p_peer_id": peer_id, "p_enabled": enabled},
    )
    return result.mappings().one_or_none()
