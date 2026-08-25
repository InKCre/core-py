import pytest

from app.business.deployment_config import DeploymentConfigManager
from app.business.extension.config import (
  EXTENSION_REGISTRY_CONFIG_KEY,
  ExtensionRegistryDeploymentConfig,
  normalize_registry_origin,
  resolve_extension_registry_origin,
)
from app.business.peer import PeerManager
from app.schemas.peer import CorePeerConfig
from app.settings import settings


@pytest.mark.parametrize(
  "value",
  [
    "ftp://registry.test",
    "https://user@registry.test",
    "https://registry.test/simple/",
    "https://registry.test?channel=preview",
    "https://registry.test#fragment",
  ],
)
def test_registry_origin_rejects_non_origin_values(value: str):
  with pytest.raises(ValueError, match="one HTTP\\(S\\) origin"):
    normalize_registry_origin(value)


def test_registry_origin_normalizes_one_trailing_slash():
  assert normalize_registry_origin(" https://registry.test/ ") == "https://registry.test"


def test_executing_peer_registry_override_wins(monkeypatch):
  monkeypatch.setattr(
    PeerManager,
    "get_current_config",
    lambda: CorePeerConfig(extension_registry_url="https://peer.registry.test"),
  )
  monkeypatch.setattr(
    DeploymentConfigManager,
    "get",
    lambda key: pytest.fail(f"deployment config must not be read: {key}"),
  )

  assert resolve_extension_registry_origin() == "https://peer.registry.test"


def test_deployment_registry_default_precedes_process_fallback(monkeypatch):
  monkeypatch.setattr(
    PeerManager,
    "get_current_config",
    lambda: CorePeerConfig(),
  )
  monkeypatch.setattr(
    DeploymentConfigManager,
    "get",
    lambda key: (
      {"extension_registry_url": "https://deployment.registry.test/"}
      if key == EXTENSION_REGISTRY_CONFIG_KEY
      else None
    ),
  )

  assert resolve_extension_registry_origin() == "https://deployment.registry.test"


def test_process_registry_origin_is_the_final_fallback(monkeypatch):
  monkeypatch.setattr(
    PeerManager,
    "get_current_config",
    lambda: CorePeerConfig(),
  )
  monkeypatch.setattr(DeploymentConfigManager, "get", lambda _key: None)

  assert resolve_extension_registry_origin() == normalize_registry_origin(
    settings.extension_registry_url
  )


def test_deployment_registry_contract_is_strict():
  assert (
    ExtensionRegistryDeploymentConfig.model_validate(
      {"extension_registry_url": "https://registry.test/"}
    ).extension_registry_url
    == "https://registry.test"
  )
  with pytest.raises(ValueError):
    ExtensionRegistryDeploymentConfig.model_validate(
      {
        "extension_registry_url": "https://registry.test",
        "unexpected": True,
      }
    )
