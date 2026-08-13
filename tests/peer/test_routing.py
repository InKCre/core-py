"""One-shot Peer routing and conservative failover semantics."""

import asyncio
import uuid

import pytest

import app.business.peer.main as peer_main
from app.business.peer import (
  CapabilityDelegationUnavailable,
  PeerManager,
  PeerOutcomeUnknown,
  PeerRequestNotExecuted,
)
from app.schemas.peer import PeerCapabilityAdvertisement, PeerInboundInterface, PeerModel


CAPABILITY = "core.test.action.v1"


def _candidate(name: str):
  return peer_main._Candidate(
    PeerModel(id=uuid.uuid4(), name=name),
    PeerCapabilityAdvertisement(
      id=CAPABILITY,
      inbound=PeerInboundInterface(protocol="core.test.protocol.v1", parameters={}),
    ),
  )


def test_any_provider_fails_over_only_after_proven_non_execution(monkeypatch):
  attempts = []
  candidates = (_candidate("unavailable"), _candidate("success"))

  class Outbound:
    def __init__(self, peer, _parameters):
      self.peer = peer

    async def execute(self, _payload):
      attempts.append(self.peer.name)
      if self.peer.name == "unavailable":
        raise PeerRequestNotExecuted("not sent")
      return {"done": True}

  monkeypatch.setattr(
    PeerManager,
    "_candidates",
    classmethod(lambda _cls, _capability, _target: candidates),
  )
  monkeypatch.setattr(
    PeerManager,
    "_OUTBOUNDS",
    {"core.test.protocol.v1": Outbound},
  )

  assert asyncio.run(PeerManager.delegate(CAPABILITY, {})) == {"done": True}
  assert attempts == ["unavailable", "success"]


def test_exact_target_and_outcome_unknown_never_fail_over(monkeypatch):
  candidates = (_candidate("first"), _candidate("second"))
  attempts = []

  class Outbound:
    def __init__(self, peer, _parameters):
      self.peer = peer

    async def execute(self, _payload):
      attempts.append(self.peer.name)
      if self.peer.name == "first":
        raise PeerOutcomeUnknown("possibly executed")
      return {"done": True}

  monkeypatch.setattr(
    PeerManager,
    "_candidates",
    classmethod(lambda _cls, _capability, _target: candidates),
  )
  monkeypatch.setattr(
    PeerManager,
    "_OUTBOUNDS",
    {"core.test.protocol.v1": Outbound},
  )

  with pytest.raises(PeerOutcomeUnknown):
    asyncio.run(PeerManager.delegate(CAPABILITY, {}))
  assert attempts == ["first"]

  class NotExecutedOutbound(Outbound):
    async def execute(self, _payload):
      attempts.append(self.peer.name)
      raise PeerRequestNotExecuted("not sent")

  attempts.clear()
  monkeypatch.setattr(
    PeerManager,
    "_OUTBOUNDS",
    {"core.test.protocol.v1": NotExecutedOutbound},
  )
  with pytest.raises(CapabilityDelegationUnavailable):
    asyncio.run(PeerManager.delegate(CAPABILITY, {}, route_to_peer=uuid.uuid4()))
  assert attempts == ["first"]
