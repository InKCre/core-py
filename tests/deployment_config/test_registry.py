import pydantic
import pytest

from app.business.deployment_config import (
  DeploymentConfigManager,
  DeploymentConfigSchemaCollisionError,
  UnknownDeploymentConfigSchemaError,
)


class FirstConfig(pydantic.BaseModel):
  value: int


class OtherConfig(pydantic.BaseModel):
  value: str


class IsolatedDeploymentConfigManager(DeploymentConfigManager):
  _contracts = {}


@pytest.fixture(autouse=True)
def clear_registry():
  IsolatedDeploymentConfigManager._contracts.clear()


def test_schema_registration_is_idempotent_only_for_the_same_model():
  IsolatedDeploymentConfigManager.register_schema("example.config.v1", FirstConfig)
  IsolatedDeploymentConfigManager.register_schema("example.config.v1", FirstConfig)

  assert IsolatedDeploymentConfigManager._contract("example.config.v1").model is FirstConfig

  with pytest.raises(DeploymentConfigSchemaCollisionError):
    IsolatedDeploymentConfigManager.register_schema(
      "example.config.v1",
      OtherConfig,
    )


def test_unknown_exact_schema_is_explicit():
  with pytest.raises(
    UnknownDeploymentConfigSchemaError,
    match="Unknown deployment config schema",
  ):
    IsolatedDeploymentConfigManager._contract("unknown.config.v1")
