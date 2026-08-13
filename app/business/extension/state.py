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


class InstalledExtension(pydantic.BaseModel):
  """Stable Host-facing projection; SQLModel and table details remain private."""

  model_config = pydantic.ConfigDict(frozen=True)

  name: str
  version: str
  enabled: tuple[uuid.UUID, ...] = ()
  nickname: str | None = None
  config: dict[str, typing.Any] = pydantic.Field(default_factory=dict)
  config_schema: dict[str, typing.Any] | None = None


StateMutation: typing.TypeAlias = Callable[[dict[str, typing.Any]], dict[str, typing.Any]]
ConfigStateMutation: typing.TypeAlias = Callable[
  [dict[str, typing.Any], dict[str, typing.Any]],
  tuple[dict[str, typing.Any], dict[str, typing.Any]],
]


class ExtensionStore(typing.Protocol):
  def list(self) -> tuple[InstalledExtension, ...]: ...

  def get(self, name: str) -> InstalledExtension | None: ...

  def install(self, name: str, version: str, nickname: str) -> InstalledExtension: ...

  def uninstall(self, name: str) -> None: ...

  def read_config(self, name: str) -> dict[str, typing.Any]: ...

  def update_config(
    self, name: str, config: dict[str, typing.Any]
  ) -> InstalledExtension: ...

  def read_state(self, name: str) -> dict[str, typing.Any]: ...

  def mutate_state(
    self,
    name: str,
    transform: StateMutation,
  ) -> dict[str, typing.Any]: ...

  def mutate_config_and_state(
    self,
    name: str,
    transform: ConfigStateMutation,
  ) -> tuple[dict[str, typing.Any], dict[str, typing.Any]]: ...

  def update_config_schema(
    self, name: str, schema: dict[str, typing.Any]
  ) -> InstalledExtension: ...

  def set_peer_enabled(
    self, name: str, peer_id: uuid.UUID, enabled: bool
  ) -> InstalledExtension: ...


class SQLExtensionStore:
  """Transactional adapter over the one canonical deployment relation."""

  def __init__(
    self, session_factory: Callable[[], sqlmodel.Session] = SessionLocal
  ) -> None:
    self._session_factory = session_factory

  @staticmethod
  def _installed(model: ExtensionModel) -> InstalledExtension:
    return InstalledExtension(
      name=model.name,
      version=model.version,
      enabled=tuple(model.enabled),
      nickname=model.nickname,
      config=dict(model.config),
      config_schema=(
        dict(model.config_schema) if model.config_schema is not None else None
      ),
    )

  def list(self) -> tuple[InstalledExtension, ...]:
    with self._session_factory() as db:
      rows = db.exec(sqlmodel.select(ExtensionModel).order_by(ExtensionModel.name)).all()
      return tuple(self._installed(row) for row in rows)

  def get(self, name: str) -> InstalledExtension | None:
    with self._session_factory() as db:
      row = db.get(ExtensionModel, name)
      return self._installed(row) if row is not None else None

  def install(self, name: str, version: str, nickname: str) -> InstalledExtension:
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
          state={},
          config_schema=None,
        )
      elif row.version != version:
        if row.enabled:
          raise ExtensionStateConflictError(
            f"Cannot change {name} while one or more peers are enabled"
          )
        if row.state:
          raise ExtensionStateConflictError(
            f"Cannot change {name} while Extension state is not empty"
          )
        row.version = version
        row.nickname = nickname
        row.config_schema = None
      else:
        row.nickname = nickname
      db.add(row)
      db.commit()
      db.refresh(row)
      return self._installed(row)

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
  ) -> InstalledExtension:
    with self._session_factory() as db:
      row = db.get(ExtensionModel, name)
      if row is None:
        raise ExtensionNotInstalledError(f"{name} is not installed")
      setattr(row, field, value)
      db.add(row)
      db.commit()
      db.refresh(row)
      return self._installed(row)

  @staticmethod
  def _locked_row(db: sqlmodel.Session, name: str) -> ExtensionModel:
    row = db.exec(
      sqlmodel.select(ExtensionModel).where(ExtensionModel.name == name).with_for_update()
    ).one_or_none()
    if row is None:
      raise ExtensionNotInstalledError(f"{name} is not installed")
    return row

  def read_config(self, name: str) -> dict[str, typing.Any]:
    with self._session_factory() as db:
      row = db.get(ExtensionModel, name)
      if row is None:
        raise ExtensionNotInstalledError(f"{name} is not installed")
      return dict(row.config)

  def update_config(self, name: str, config: dict[str, typing.Any]) -> InstalledExtension:
    return self._update_json(name, "config", config)

  def read_state(self, name: str) -> dict[str, typing.Any]:
    with self._session_factory() as db:
      row = db.get(ExtensionModel, name)
      if row is None:
        raise ExtensionNotInstalledError(f"{name} is not installed")
      return dict(row.state)

  def mutate_state(
    self,
    name: str,
    transform: StateMutation,
  ) -> dict[str, typing.Any]:
    with self._session_factory() as db:
      row = self._locked_row(db, name)
      updated = transform(dict(row.state))
      if not isinstance(updated, dict):
        raise TypeError("Extension state mutation must return an object")
      row.state = dict(updated)
      db.add(row)
      db.commit()
      return dict(row.state)

  def mutate_config_and_state(
    self,
    name: str,
    transform: ConfigStateMutation,
  ) -> tuple[dict[str, typing.Any], dict[str, typing.Any]]:
    with self._session_factory() as db:
      row = self._locked_row(db, name)
      config, state = transform(dict(row.config), dict(row.state))
      if not isinstance(config, dict) or not isinstance(state, dict):
        raise TypeError("Extension config/state mutation must return two objects")
      row.config = dict(config)
      row.state = dict(state)
      db.add(row)
      db.commit()
      return dict(row.config), dict(row.state)

  def update_config_schema(
    self, name: str, schema: dict[str, typing.Any]
  ) -> InstalledExtension:
    return self._update_json(name, "config_schema", schema)

  def set_peer_enabled(
    self, name: str, peer_id: uuid.UUID, enabled: bool
  ) -> InstalledExtension:
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
      return InstalledExtension.model_validate(dict(row))
