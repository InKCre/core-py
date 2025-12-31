__all__ = [
  "ClientManager",
]

import sqlalchemy.dialects.postgresql
import sqlmodel
from app.engine import SessionLocal
from app.settings import settings
from app.schemas.client.main import ClientModel, ClientID
from libs.obsrv.main import get_logger


LOGGER = get_logger().getChild(__name__)


class ClientManager:
  """Manages client registration and lookup."""

  @classmethod
  def register_self(cls) -> ClientModel:
    """Register or update the current client in the database.

    Uses upsert to handle both initial registration and updates.
    Called during application startup.
    """
    with SessionLocal() as db:
      stmt = sqlalchemy.dialects.postgresql.insert(ClientModel).values(
        id=settings.client_id,
        name=settings.client_name,
        rest_api_url=settings.client_base_url,
      )
      stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_=dict(
          name=stmt.excluded.name,
          rest_api_url=stmt.excluded.rest_api_url,
        ),
      )
      db.exec(stmt)  # type: ignore
      db.commit()

      # Fetch and return the registered client
      client = db.exec(
        sqlmodel.select(ClientModel).where(ClientModel.id == settings.client_id)
      ).one()

      LOGGER.info(f"Client registered: {client.name} ({client.id})")
      return client

  @classmethod
  def get_current_client_id(cls) -> ClientID:
    """Get the current client's ID."""
    return settings.client_id

  @classmethod
  def get(cls, client_id: ClientID) -> ClientModel | None:
    """Get a client by ID."""
    with SessionLocal() as db:
      return db.exec(
        sqlmodel.select(ClientModel).where(ClientModel.id == client_id)
      ).first()

  @classmethod
  def get_all(cls) -> tuple[ClientModel, ...]:
    """Get all registered clients."""
    with SessionLocal() as db:
      return tuple(db.exec(sqlmodel.select(ClientModel)).all())
