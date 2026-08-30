"""Persisted Sink catalog, instances, and Peer-local lifecycle."""

import logging
import typing

import fastapi
import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlmodel

from app.engine import SessionLocal
from app.schemas.peer import PeerRef
from app.schemas.sink import SinkID, SinkModel, SinkTypeID, SinkTypeModel

from .errors import (
  DuplicateSinkRegistrationError,
  SinkNotFoundError,
  SinkStateConflictError,
  UnknownSinkTypeError,
)

if typing.TYPE_CHECKING:
  from .base import SinkBase


logger = logging.getLogger(__name__)


class SinkManager:
  """Own Sink registration, persistence, and local instance realization."""

  _SINK_CLASSES: dict[SinkTypeID, type["SinkBase"]] = {}
  _running: dict[SinkID, "SinkBase"] = {}
  _app: fastapi.FastAPI | None = None

  @classmethod
  def register_sink_type(cls, sink_cls: type["SinkBase"]) -> None:
    existing = cls._SINK_CLASSES.get(sink_cls.__sinktype__)
    if existing is sink_cls:
      return
    if existing is not None:
      raise DuplicateSinkRegistrationError(
        f"Sink type {sink_cls.__sinktype__!r} is already registered"
      )
    cls._SINK_CLASSES[sink_cls.__sinktype__] = sink_cls

  @classmethod
  def sync_sink_types(cls) -> None:
    with SessionLocal() as db:
      for sink_cls in cls._SINK_CLASSES.values():
        statement = sqlalchemy.dialects.postgresql.insert(SinkTypeModel).values(
          id=sink_cls.__sinktype__,
          description=sink_cls.__doc__ or "No description.",
          config_schema=sink_cls.__configschema__,
        )
        statement = statement.on_conflict_do_update(
          index_elements=["id"],
          set_={
            "description": statement.excluded.description,
            "config_schema": statement.excluded.config_schema,
          },
        )
        db.exec(statement)  # type: ignore
      db.commit()

  @classmethod
  def list_types(cls) -> tuple[SinkTypeModel, ...]:
    with SessionLocal() as db:
      return tuple(db.exec(sqlmodel.select(SinkTypeModel).order_by(SinkTypeModel.id)).all())

  @classmethod
  def list(cls) -> tuple[SinkModel, ...]:
    with SessionLocal() as db:
      return tuple(
        db.exec(sqlmodel.select(SinkModel).order_by(sqlmodel.col(SinkModel.id))).all()
      )

  @classmethod
  def get(cls, sink_id: SinkID) -> SinkModel:
    with SessionLocal() as db:
      sink = db.get(SinkModel, sink_id)
    if sink is None:
      raise SinkNotFoundError(f"Sink {sink_id} does not exist")
    return sink

  @classmethod
  def create(
    cls,
    sink_type: SinkTypeID,
    *,
    nickname: str | None = None,
    config: dict[str, typing.Any] | None = None,
  ) -> SinkModel:
    sink_cls = cls._require_type(sink_type)
    normalized = sink_cls.__configcls__.model_validate(config or {}).model_dump(mode="json")
    with SessionLocal() as db:
      sink = SinkModel(type=sink_type, nickname=nickname, config=normalized)
      db.add(sink)
      db.commit()
      db.refresh(sink)
      return sink

  @classmethod
  def update_config(
    cls,
    sink_id: SinkID,
    value: dict[str, typing.Any],
  ) -> SinkModel:
    current = cls.get(sink_id)
    sink_cls = cls._require_type(current.type)
    normalized = sink_cls.__configcls__.model_validate(value).model_dump(mode="json")
    with SessionLocal() as db:
      sink = db.get(SinkModel, sink_id)
      if sink is None:
        raise SinkNotFoundError(f"Sink {sink_id} does not exist")
      sink.config = normalized
      db.add(sink)
      db.commit()
      db.refresh(sink)
    running = cls._running.get(sink_id)
    if running is not None:
      running.update_config(normalized)
    return sink

  @classmethod
  def delete(cls, sink_id: SinkID) -> None:
    with SessionLocal() as db:
      sink = db.get(SinkModel, sink_id)
      if sink is None:
        raise SinkNotFoundError(f"Sink {sink_id} does not exist")
      if sink.enabled or sink_id in cls._running:
        raise SinkStateConflictError("Disable the Sink before deleting it")
      db.delete(sink)
      db.commit()

  @classmethod
  async def enable(cls, sink_id: SinkID, peer: PeerRef) -> SinkModel:
    sink = cls._set_peer_enabled(sink_id, peer, True)
    if sink_id in cls._running:
      return sink
    if cls._app is None:
      raise SinkStateConflictError("Sink runtime has not started")
    sink_cls = cls._require_type(sink.type)
    instance = sink_cls(sink)
    await instance.on_start(cls._app)
    cls._running[sink_id] = instance
    return sink

  @classmethod
  async def disable(cls, sink_id: SinkID, peer: PeerRef) -> SinkModel:
    sink = cls._set_peer_enabled(sink_id, peer, False)
    running = cls._running.get(sink_id)
    if running is not None:
      await running.on_close()
      cls._running.pop(sink_id, None)
    return sink

  @classmethod
  async def startup(cls, app: fastapi.FastAPI, peer: PeerRef) -> None:
    cls._app = app
    cls.sync_sink_types()
    for sink in cls.list():
      if sink.id is None or peer not in sink.enabled:
        continue
      try:
        await cls.enable(sink.id, peer)
      except Exception:
        logger.exception("Sink failed to start", extra={"sink": sink.id, "type": sink.type})

  @classmethod
  async def shutdown(cls) -> None:
    for sink_id, instance in tuple(cls._running.items())[::-1]:
      try:
        await instance.on_close()
      except Exception:
        logger.exception("Sink failed to close", extra={"sink": sink_id})
      else:
        cls._running.pop(sink_id, None)
    cls._app = None

  @classmethod
  def _require_type(cls, sink_type: SinkTypeID) -> type["SinkBase"]:
    sink_cls = cls._SINK_CLASSES.get(sink_type)
    if sink_cls is None:
      raise UnknownSinkTypeError(f"Sink type {sink_type!r} is not registered")
    return sink_cls

  @classmethod
  def _set_peer_enabled(
    cls,
    sink_id: SinkID,
    peer: PeerRef,
    enabled: bool,
  ) -> SinkModel:
    with SessionLocal() as db:
      sink = db.exec(
        sqlmodel.select(SinkModel).where(SinkModel.id == sink_id).with_for_update()
      ).one_or_none()
      if sink is None:
        raise SinkNotFoundError(f"Sink {sink_id} does not exist")
      peers = list(sink.enabled)
      if enabled and peer not in peers:
        peers.append(peer)
      elif not enabled and peer in peers:
        peers.remove(peer)
      sink.enabled = peers
      db.add(sink)
      db.commit()
      db.refresh(sink)
      return sink
