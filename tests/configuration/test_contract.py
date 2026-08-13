import pydantic
import pytest

from app.configuration import ConfigContract


class NestedConfig(pydantic.BaseModel):
  enabled: bool


class ExampleConfig(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid")

  name: str
  retries: int = pydantic.Field(default=3, ge=0)
  nested: NestedConfig


def test_complete_validation_and_normalization_are_model_owned():
  contract = ConfigContract(ExampleConfig)

  validated = contract.validate({"name": "alpha", "nested": {"enabled": True}})

  assert validated == ExampleConfig(
    name="alpha",
    retries=3,
    nested=NestedConfig(enabled=True),
  )
  assert contract.normalize(validated) == {
    "name": "alpha",
    "retries": 3,
    "nested": {"enabled": True},
  }


def test_prepare_patch_is_shallow_then_validates_the_complete_value():
  contract = ConfigContract(ExampleConfig)
  current = {
    "name": "alpha",
    "retries": 3,
    "nested": {"enabled": True},
  }

  patched = contract.prepare_patch(current, {"name": "beta", "retries": 0})

  assert patched.name == "beta"
  assert patched.retries == 0
  assert patched.nested.enabled is True

  with pytest.raises(pydantic.ValidationError):
    contract.prepare_patch(current, {"nested": {}})


def test_json_schema_is_a_projection_of_the_authoritative_model():
  contract = ConfigContract(ExampleConfig)

  assert contract.json_schema() == ExampleConfig.model_json_schema()


def test_complete_validation_rejects_unknown_fields():
  contract = ConfigContract(ExampleConfig)

  with pytest.raises(pydantic.ValidationError):
    contract.validate(
      {
        "name": "alpha",
        "nested": {"enabled": True},
        "unowned": "value",
      }
    )
