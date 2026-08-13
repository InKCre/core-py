"""Deployment-scoped config HTTP resource."""

__all__ = ["ROUTER"]

import typing

import fastapi
import pydantic

from app.business.deployment_config import (
  DeploymentConfigManager,
  DeploymentConfigNotFoundError,
  InvalidPersistedDeploymentConfigError,
  UnknownDeploymentConfigSchemaError,
)
from app.schemas.deployment_config import (
  DeploymentConfigKey,
  DeploymentConfigReplaceForm,
  DeploymentConfigView,
)


ROUTER = fastapi.APIRouter(prefix="/configs", tags=["config"])


def _unusable_config(error: Exception) -> typing.NoReturn:
  raise fastapi.HTTPException(
    status_code=fastapi.status.HTTP_409_CONFLICT,
    detail=str(error),
  ) from error


@ROUTER.get("/{key}", response_model_by_alias=True)
def get_config(key: DeploymentConfigKey) -> DeploymentConfigView:
  try:
    config = DeploymentConfigManager.read(key)
  except (
    UnknownDeploymentConfigSchemaError,
    InvalidPersistedDeploymentConfigError,
  ) as error:
    _unusable_config(error)
  if config is None:
    raise fastapi.HTTPException(
      status_code=fastapi.status.HTTP_404_NOT_FOUND,
      detail=f"Deployment config {key!r} not found",
    )
  return config


@ROUTER.put("/{key}", response_model_by_alias=True)
def replace_config(
  key: DeploymentConfigKey,
  body: DeploymentConfigReplaceForm,
) -> DeploymentConfigView:
  try:
    return DeploymentConfigManager.replace(key, body.schema_id, body.value)
  except UnknownDeploymentConfigSchemaError as error:
    raise fastapi.HTTPException(
      status_code=fastapi.status.HTTP_422_UNPROCESSABLE_CONTENT,
      detail=str(error),
    ) from error
  except pydantic.ValidationError as error:
    raise fastapi.HTTPException(
      status_code=fastapi.status.HTTP_422_UNPROCESSABLE_CONTENT,
      detail=error.errors(),
    ) from error


@ROUTER.patch("/{key}", response_model_by_alias=True)
def patch_config(
  key: DeploymentConfigKey,
  body: dict[str, typing.Any] = fastapi.Body(...),
) -> DeploymentConfigView:
  try:
    return DeploymentConfigManager.patch(key, body)
  except DeploymentConfigNotFoundError as error:
    raise fastapi.HTTPException(
      status_code=fastapi.status.HTTP_404_NOT_FOUND,
      detail=str(error),
    ) from error
  except (
    UnknownDeploymentConfigSchemaError,
    InvalidPersistedDeploymentConfigError,
  ) as error:
    _unusable_config(error)
  except pydantic.ValidationError as error:
    raise fastapi.HTTPException(
      status_code=fastapi.status.HTTP_422_UNPROCESSABLE_CONTENT,
      detail=error.errors(),
    ) from error
