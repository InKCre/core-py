"""Deployment-scoped configuration registry and persistence."""

import typing

import pydantic
import sqlalchemy.dialects.postgresql
import sqlmodel

from app.configuration import ConfigContract
from app.engine import SessionLocal
from app.schemas.deployment_config import (
  DeploymentConfigKey,
  DeploymentConfigModel,
  DeploymentConfigSchemaID,
  DeploymentConfigView,
)


class UnknownDeploymentConfigSchemaError(LookupError):
  """The current peer has no validator for an exact persisted schema ID."""


class DeploymentConfigSchemaCollisionError(ValueError):
  """Two different local models claimed the same exact schema ID."""


class DeploymentConfigNotFoundError(LookupError):
  """A patch addressed a deployment config that does not exist."""


class InvalidPersistedDeploymentConfigError(RuntimeError):
  """A stored value does not satisfy its stored exact schema contract."""


class DeploymentConfigManager:
  """Own exact schema registration and the shared ``configs`` relation."""

  _contracts: dict[DeploymentConfigSchemaID, ConfigContract] = {}

  @classmethod
  def register_schema(
    cls,
    schema_id: DeploymentConfigSchemaID,
    model: type[pydantic.BaseModel],
  ) -> None:
    """Register one exact schema ID idempotently for the same model."""
    existing = cls._contracts.get(schema_id)
    if existing is not None:
      if existing.model is model:
        return
      raise DeploymentConfigSchemaCollisionError(
        f"Deployment config schema {schema_id!r} is already registered "
        f"by {existing.model.__qualname__}"
      )
    cls._contracts[schema_id] = ConfigContract(model)

  @classmethod
  def _contract(
    cls,
    schema_id: DeploymentConfigSchemaID,
  ) -> ConfigContract:
    try:
      return cls._contracts[schema_id]
    except KeyError as error:
      raise UnknownDeploymentConfigSchemaError(
        f"Unknown deployment config schema: {schema_id}"
      ) from error

  @classmethod
  def _validate_record(
    cls,
    record: DeploymentConfigModel,
  ) -> pydantic.BaseModel:
    contract = cls._contract(record.schema_id)
    try:
      return contract.validate(record.value)
    except pydantic.ValidationError as error:
      raise InvalidPersistedDeploymentConfigError(
        f"Deployment config {record.key!r} does not satisfy {record.schema_id!r}"
      ) from error

  @classmethod
  def _view(cls, record: DeploymentConfigModel) -> DeploymentConfigView:
    value = cls._validate_record(record).model_dump(mode="json")
    return DeploymentConfigView(
      key=record.key,
      schema=record.schema_id,
      value=value,
      created_at=record.created_at,
      updated_at=record.updated_at,
    )

  @classmethod
  def get(cls, key: DeploymentConfigKey) -> pydantic.BaseModel | None:
    """Load and validate one config, returning its owner-defined typed value."""
    with SessionLocal() as db:
      record = db.get(DeploymentConfigModel, key)
      if record is None:
        return None
      return cls._validate_record(record)

  @classmethod
  def read(cls, key: DeploymentConfigKey) -> DeploymentConfigView | None:
    """Read one fully validated config with persistence metadata."""
    with SessionLocal() as db:
      record = db.get(DeploymentConfigModel, key)
      if record is None:
        return None
      return cls._view(record)

  @classmethod
  def replace(
    cls,
    key: DeploymentConfigKey,
    schema_id: DeploymentConfigSchemaID,
    complete_value: dict[str, typing.Any],
  ) -> DeploymentConfigView:
    """Atomically upsert a complete value and, if needed, its schema."""
    contract = cls._contract(schema_id)
    normalized = contract.normalize(complete_value)

    with SessionLocal() as db:
      statement = sqlalchemy.dialects.postgresql.insert(DeploymentConfigModel).values(
        key=key,
        schema_id=schema_id,
        value=normalized,
      )
      statement = statement.on_conflict_do_update(
        index_elements=[DeploymentConfigModel.key],
        set_={
          DeploymentConfigModel.__table__.c.schema: statement.excluded.schema,  # pyrefly: ignore[missing-attribute]
          DeploymentConfigModel.__table__.c.value: statement.excluded.value,  # pyrefly: ignore[missing-attribute]
        },
      )
      db.exec(statement)  # type: ignore
      db.commit()
      record = db.get(DeploymentConfigModel, key)
      if record is None:  # pragma: no cover - database upsert invariant
        raise RuntimeError(f"Deployment config upsert did not return {key!r}")
      return cls._view(record)

  @classmethod
  def patch(
    cls,
    key: DeploymentConfigKey,
    partial_value: dict[str, typing.Any],
  ) -> DeploymentConfigView:
    """Shallow-patch an existing row without changing its schema contract."""
    with SessionLocal() as db:
      statement = (
        sqlmodel.select(DeploymentConfigModel)
        .where(DeploymentConfigModel.key == key)
        .with_for_update()
      )
      record = db.exec(statement).first()
      if record is None:
        raise DeploymentConfigNotFoundError(f"Deployment config {key!r} does not exist")

      contract = cls._contract(record.schema_id)
      try:
        validated_current = contract.validate(record.value)
      except pydantic.ValidationError as error:
        raise InvalidPersistedDeploymentConfigError(
          f"Deployment config {key!r} does not satisfy {record.schema_id!r}"
        ) from error
      validated = contract.prepare_patch(validated_current, partial_value)
      record.value = validated.model_dump(mode="json")
      db.add(record)
      db.commit()
      db.refresh(record)
      return cls._view(record)
