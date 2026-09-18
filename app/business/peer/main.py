"""Peer identity, local inbound publication, discovery, and delegation."""

from __future__ import annotations

from dataclasses import dataclass
import datetime
import logging
import random
import typing

import pydantic

from app.configuration import ConfigContract
from app.engine import SessionLocal
from app.schemas.ai import JSONValue
from app.schemas.peer import (
  PEER_HTTP_PROTOCOL,
  CapabilityID,
  CorePeerConfig,
  PeerCapabilityAdvertisement,
  PeerModel,
  PeerRef,
  normalize_capability_snapshot,
)
from app.settings import settings

from .contracts import (
  CapabilityDelegationUnavailable,
  DuplicatePeerRegistrationError,
  PeerInbound,
  PeerOutcomeUnknown,
  PeerOutboundFactory,
  PeerProtocolConfigurationError,
  PeerRequestNotExecuted,
)
from .http import PeerHTTPOutbound
from app.persistence.peer.uow import peer_uow


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _Candidate:
  peer: PeerModel
  advertisement: PeerCapabilityAdvertisement


class PeerManager:
  """Own Peer facts, local inbound registry, discovery, and one-shot routing."""

  _INBOUNDS: dict[CapabilityID, PeerInbound] = {}
  _OUTBOUNDS: dict[str, PeerOutboundFactory] = {}
  _random: random.Random = random.SystemRandom()
  _config_contract = ConfigContract(CorePeerConfig)

  @classmethod
  async def register_self(cls) -> PeerModel:
    """Upsert runtime-owned identity/schema without changing owner configuration."""
    async with peer_uow() as peers:
      peer = await peers.register(
        settings.peer_id, settings.peer_name, cls._config_contract.json_schema()
      )
    logger.info("Peer registered", extra={"peer": str(peer.id), "name": peer.name})
    return peer

  @classmethod
  def get_current_peer_ref(cls) -> PeerRef:
    return settings.peer_id

  @classmethod
  def get_current_config(cls) -> CorePeerConfig:
    """Load the current Peer owner's complete validated configuration."""
    peer = cls.get(cls.get_current_peer_ref())
    if peer is None:
      raise RuntimeError("Current Peer must be registered before reading config")
    try:
      return cls._config_contract.validate(peer.config)
    except pydantic.ValidationError as error:
      raise ValueError("Current Peer config is invalid") from error

  @classmethod
  async def get_current_config_async(cls) -> CorePeerConfig:
    peer = await cls.get_async(cls.get_current_peer_ref())
    if peer is None:
      raise RuntimeError("Current Peer must be registered before reading config")
    try:
      return cls._config_contract.validate(peer.config)
    except pydantic.ValidationError as error:
      raise ValueError("Current Peer config is invalid") from error

  @classmethod
  def get(cls, peer: PeerRef) -> PeerModel | None:
    with SessionLocal() as db:
      return db.get(PeerModel, peer)

  @classmethod
  async def get_async(cls, peer: PeerRef) -> PeerModel | None:
    async with peer_uow() as peers:
      return await peers.get(peer)

  @classmethod
  async def get_all(cls) -> tuple[PeerModel, ...]:
    async with peer_uow() as peers:
      return await peers.get_all()

  @classmethod
  async def get_with_lease(cls, peer: PeerRef) -> dict[str, typing.Any] | None:
    async with peer_uow() as peers:
      rows, _ = await peers.with_leases(peer_id=peer)
    return rows[0] if rows else None

  @classmethod
  async def list_with_leases(
    cls, *, limit: int | None = None, cursor: PeerRef | None = None
  ) -> tuple[list[dict[str, typing.Any]], PeerRef | None]:
    async with peer_uow() as peers:
      return await peers.with_leases(limit=limit, cursor=cursor)

  @classmethod
  def register_inbound(cls, inbound: PeerInbound) -> bool:
    """Register one inbound and report whether this call added it."""
    existing = cls._INBOUNDS.get(inbound.capability)
    if existing is inbound or existing == inbound:
      return False
    if existing is not None:
      raise DuplicatePeerRegistrationError(
        f"Capability inbound {inbound.capability!r} is already registered"
      )
    cls._INBOUNDS[inbound.capability] = inbound
    return True

  @classmethod
  def unregister_inbound(cls, capability: CapabilityID) -> None:
    cls._INBOUNDS.pop(capability, None)

  @classmethod
  def register_outbound(
    cls,
    protocol: str,
    factory: PeerOutboundFactory,
  ) -> None:
    existing = cls._OUTBOUNDS.get(protocol)
    if existing is factory:
      return
    if existing is not None:
      raise DuplicatePeerRegistrationError(
        f"Peer outbound {protocol!r} is already registered"
      )
    cls._OUTBOUNDS[protocol] = factory

  @classmethod
  def setup_builtin_outbounds(cls) -> None:
    cls.register_outbound(PEER_HTTP_PROTOCOL, PeerHTTPOutbound)

  @classmethod
  async def publish_self(cls) -> PeerModel:
    """Replace this Peer-owned capability snapshot from current config/registry."""
    async with peer_uow() as peers:
      peer = await peers.get(settings.peer_id, for_update=True)
      if peer is None:
        raise RuntimeError("Current Peer must be registered before publication")
      try:
        config = cls._config_contract.validate(peer.config)
      except pydantic.ValidationError as error:
        raise ValueError("Current Peer config is invalid") from error
      advertisements = normalize_capability_snapshot(
        advertisement
        for inbound in cls._INBOUNDS.values()
        if (advertisement := inbound.advertise(config)) is not None
      )
      normalized = [
        typing.cast(dict[str, JSONValue], advertisement.model_dump(mode="json"))
        for advertisement in advertisements
      ]
      if peer.capabilities != normalized:
        peer.capabilities = normalized
        await peers.save(peer)
    return peer

  @classmethod
  async def renew_self_lease(cls, ttl_seconds: int) -> datetime.datetime:
    """Renew liveness through the database-time helper."""
    if ttl_seconds <= 0:
      raise ValueError("Peer lease TTL must be positive")
    async with peer_uow() as peers:
      expiry = await peers.renew_lease(settings.peer_id, ttl_seconds)
    return expiry

  @classmethod
  async def refresh_self(cls, ttl_seconds: int) -> PeerModel:
    """Refresh advertisement, then renew its route lease."""
    peer = await cls.publish_self()
    peer.lease_expires_at = await cls.renew_self_lease(ttl_seconds)
    return peer

  @classmethod
  async def clear_self_lease(cls) -> None:
    async with peer_uow() as peers:
      await peers.clear_lease(settings.peer_id)

  @classmethod
  async def delegate(
    cls,
    capability: CapabilityID,
    payload: JSONValue,
    *,
    route_to_peer: PeerRef | None = None,
  ) -> JSONValue:
    """Execute through one eligible Peer, failing over only after non-execution."""
    candidates = await cls._candidates(capability, route_to_peer)
    attempted = 0
    for candidate in candidates:
      factory = cls._OUTBOUNDS.get(candidate.advertisement.inbound.protocol)
      if factory is None:  # candidate eligibility is rechecked defensively
        continue
      try:
        outbound = factory(
          candidate.peer,
          candidate.advertisement.inbound.parameters,
        )
      except PeerProtocolConfigurationError:
        continue
      attempted += 1
      try:
        return await outbound.execute(payload)
      except PeerRequestNotExecuted:
        if route_to_peer is not None:
          break
        continue
      except PeerOutcomeUnknown:
        raise
    raise CapabilityDelegationUnavailable(
      f"No eligible Peer completed capability {capability!r}; attempted={attempted}"
    )

  @classmethod
  async def _candidates(
    cls,
    capability: CapabilityID,
    route_to_peer: PeerRef | None,
  ) -> tuple[_Candidate, ...]:
    async with peer_uow() as peers_repository:
      peers = await peers_repository.candidates(settings.peer_id, route_to_peer)

    candidates: list[_Candidate] = []
    for peer in peers:
      try:
        snapshots = peer.capability_snapshot()
      except (pydantic.ValidationError, ValueError):
        logger.warning(
          "Skipping malformed Peer capability snapshot",
          extra={"peer": str(peer.id)},
        )
        continue
      for advertisement in snapshots:
        if (
          advertisement.id == capability
          and advertisement.inbound.protocol in cls._OUTBOUNDS
        ):
          candidates.append(_Candidate(peer, advertisement))
          break

    if route_to_peer is None:
      cls._random.shuffle(candidates)
    return tuple(candidates)
