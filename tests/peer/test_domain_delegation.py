"""Typed domain codecs around opaque Peer delegation."""

import asyncio
import uuid

from app.business.extension import ExtensionManager
from app.business.extension.main import EXTENSION_MANAGEMENT_CAPABILITY
from app.business.organization import OrganizationManager, RUMINATION_CAPABILITY
from app.business.peer import PeerManager
from app.business.semantic_retrieval import (
  SEMANTIC_RETRIEVAL_CAPABILITY,
  SemanticRetrievalManager,
)
from app.schemas.extension.main import EnableExtensionCommand


def test_semantic_retrieval_delegates_typed_request_to_exact_peer(monkeypatch):
  target = uuid.uuid4()
  captured = {}

  async def delegate(_cls, capability, payload, *, route_to_peer=None):
    captured.update(
      capability=capability,
      payload=payload,
      route_to_peer=route_to_peer,
    )
    return {
      "status": 200,
      "headers": {},
      "body": {"profile": 7, "metric": "cosine", "matches": []},
    }

  monkeypatch.setattr(PeerManager, "delegate", classmethod(delegate))

  result = asyncio.run(
    SemanticRetrievalManager.retrieve(
      "dynamic properties",
      profile=7,
      route_to_peer=target,
    )
  )

  assert result.profile == 7
  assert captured["capability"] == SEMANTIC_RETRIEVAL_CAPABILITY
  assert captured["route_to_peer"] == target
  body = captured["payload"]["body"]
  assert body["query"] == "dynamic properties"
  assert body["profile"] == 7
  assert body["options"]["limit"] == 20
  assert body["options"]["min_score"] is None
  assert set(body["options"]["entity_types"]) == {"block", "relation"}


def test_rumination_delegates_and_accepts_only_empty_204(monkeypatch):
  target = uuid.uuid4()
  captured = {}

  async def delegate(_cls, capability, payload, *, route_to_peer=None):
    captured.update(
      capability=capability,
      payload=payload,
      route_to_peer=route_to_peer,
    )
    return {"status": 204, "headers": {}}

  monkeypatch.setattr(PeerManager, "delegate", classmethod(delegate))

  assert asyncio.run(OrganizationManager.ruminate(42, route_to_peer=target)) is None
  assert captured == {
    "capability": RUMINATION_CAPABILITY,
    "payload": {"body": {"block": 42}},
    "route_to_peer": target,
  }


def test_extension_management_is_exact_target_delegation(monkeypatch):
  target = uuid.uuid4()
  captured = {}

  async def delegate(_cls, capability, payload, *, route_to_peer=None):
    captured.update(
      capability=capability,
      payload=payload,
      route_to_peer=route_to_peer,
    )
    return {
      "status": 200,
      "headers": {},
      "body": {
        "id": "rss",
        "version": "1.0.0",
        "enabled": [str(target)],
        "nickname": "RSS",
        "config": {},
        "config_schema": None,
      },
    }

  monkeypatch.setattr(PeerManager, "delegate", classmethod(delegate))

  result = asyncio.run(
    ExtensionManager.manage(
      EnableExtensionCommand(action="enable", extension="rss"),
      route_to_peer=target,
    )
  )

  assert result.id == "rss"
  assert captured == {
    "capability": EXTENSION_MANAGEMENT_CAPABILITY,
    "payload": {
      "body": {"action": "enable", "extension": "rss"},
    },
    "route_to_peer": target,
  }
