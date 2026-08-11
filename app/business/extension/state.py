"""Semantic deployment-state port for the canonical extensions relation."""

from __future__ import annotations

from collections.abc import Callable
import typing
import uuid

import pydantic
import sqlalchemy
import sqlmodel

from app.database_contract.constants import PROTOCOL_SCHEMA
from app.engine import SessionLocal
from app.schemas.extension import ExtensionModel

from .errors import ExtensionNotInstalledError, ExtensionStateConflictError


class ExtensionState(pydantic.BaseModel):
  """Stable Host-facing projection; SQLModel and table details remain private."""

  model_config = pydantic.ConfigDict(frozen=True)

  name: str
  version: str
  enabled: tuple[uuid.UUID, ...] = ()
  nickname: str | None = None
  config: dict[str, typing.Any] = pydantic.Field(default_factory=dict)
  config_schema: dict[str, typing.Any] | None = None


class ExtensionStateStore(typing.Protocol):
  def list(self) -> tuple[ExtensionState, ...]: ...

  def get(self, name: str) -> ExtensionState | None: ...

  def install(self, name: str, version: str, nickname: str) -> ExtensionState: ...

  def uninstall(self, name: str) -> None: ...

  def update_config(self, name: str, config: dict[str, typing.Any]) -> ExtensionState: ...

  def update_config_schema(
    self, name: str, schema: dict[str, typing.Any]
  ) -> ExtensionState: ...

  def set_peer_enabled(
    self, name: str, peer_id: uuid.UUID, enabled: bool
  ) -> ExtensionState: ...


class SQLExtensionStateStore:
  """Transactional adapter over the one canonical deployment relation."""

  def __init__(
    self, session_factory: Callable[[], sqlmodel.Session] = SessionLocal
  ) -> None:
    self._session_factory = session_factory

  @staticmethod
  def _state(model: ExtensionModel) -> ExtensionState:
    return ExtensionState(
      name=model.name,
      version=model.version,
      enabled=tuple(model.enabled),
      nickname=model.nickname,
      config=dict(model.config),
      config_schema=(
        dict(model.config_schema) if model.config_schema is not None else None
      ),
    )

  def list(self) -> tuple[ExtensionState, ...]:
    with self._session_factory() as db:
      rows = db.exec(sqlmodel.select(ExtensionModel).order_by(ExtensionModel.name)).all()
      return tuple(self._state(row) for row in rows)

  def get(self, name: str) -> ExtensionState | None:
    with self._session_factory() as db:
      row = db.get(ExtensionModel, name)
      return self._state(row) if row is not None else None

  def install(self, name: str, version: str, nickname: str) -> ExtensionState:
    with self._session_factory() as db:
      locked = (
        db.connection()
        .execute(
          sqlalchemy.text("SELECT pg_try_advisory_xact_lock(hashtextextended(:name, 0))"),
          {"name": name},
        )
        .scalar_one()
      )
      if not locked:
        raise ExtensionStateConflictError(
          f"Another install operation for {name} is already in progress"
        )
      row = db.exec(
        sqlmodel.select(ExtensionModel).where(ExtensionModel.name == name).with_for_update()
      ).one_or_none()
      if row is None:
        row = ExtensionModel(
          name=name,
          version=version,
          enabled=[],
          nickname=nickname,
          config={},
          config_schema=None,
        )
      elif row.version != version:
        if row.enabled:
          raise ExtensionStateConflictError(
            f"Cannot change {name} while one or more peers are enabled"
          )
        row.version = version
        row.nickname = nickname
        row.config_schema = None
      else:
        row.nickname = nickname
      db.add(row)
      db.commit()
      db.refresh(row)
      return self._state(row)

  def uninstall(self, name: str) -> None:
    with self._session_factory() as db:
      row = db.exec(
        sqlmodel.select(ExtensionModel).where(ExtensionModel.name == name).with_for_update()
      ).one_or_none()
      if row is None:
        raise ExtensionNotInstalledError(f"{name} is not installed")
      if row.enabled:
        raise ExtensionStateConflictError(
          f"Cannot uninstall {name} while one or more peers are enabled"
        )
      db.delete(row)
      db.commit()

  def _update_json(
    self,
    name: str,
    field: typing.Literal["config", "config_schema"],
    value: dict[str, typing.Any],
  ) -> ExtensionState:
    with self._session_factory() as db:
      row = db.get(ExtensionModel, name)
      if row is None:
        raise ExtensionNotInstalledError(f"{name} is not installed")
      setattr(row, field, value)
      db.add(row)
      db.commit()
      db.refresh(row)
      return self._state(row)

  def update_config(self, name: str, config: dict[str, typing.Any]) -> ExtensionState:
    return self._update_json(name, "config", config)

  def update_config_schema(
    self, name: str, schema: dict[str, typing.Any]
  ) -> ExtensionState:
    return self._update_json(name, "config_schema", schema)

  def set_peer_enabled(
    self, name: str, peer_id: uuid.UUID, enabled: bool
  ) -> ExtensionState:
    """Use the shared atomic RPC; Core never performs array read-modify-write."""
    statement = sqlalchemy.text(
      f"SELECT * FROM {PROTOCOL_SCHEMA}.set_extension_peer_enabled("
      ":p_name, :p_peer_id, :p_enabled)"
    )
    with self._session_factory() as db:
      row = (
        db.connection()
        .execute(
          statement,
          {
            "p_name": name,
            "p_peer_id": peer_id,
            "p_enabled": enabled,
          },
        )
        .mappings()
        .one_or_none()
      )
      if row is None:
        raise ExtensionNotInstalledError(f"{name} is not installed")
      db.commit()
      return ExtensionState.model_validate(dict(row))
