"""Peer identity, local inbound publication, discovery, and delegation."""

from __future__ import annotations

from dataclasses import dataclass
import datetime
import logging
import random
import typing

import pydantic
import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlmodel

from app.configuration import ConfigContract
from app.database_contract import PROTOCOL_SCHEMA
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
  def register_self(cls) -> PeerModel:
    """Upsert identity/schema while preserving owner-authored config and runtime state."""
    config_schema = typing.cast(
      dict[str, JSONValue],
      cls._config_contract.json_schema(),
    )
    with SessionLocal() as db:
      statement = sqlalchemy.dialects.postgresql.insert(PeerModel).values(
        id=settings.peer_id,
        name=settings.peer_name,
        labels=[],
        config={},
        config_schema=config_schema,
        capabilities=[],
      )
      statement = statement.on_conflict_do_update(
        index_elements=["id"],
        set_={
          "name": statement.excluded.name,
          "config_schema": statement.excluded.config_schema,
        },
      )
      db.exec(statement)  # type: ignore
      db.commit()
      peer = db.get(PeerModel, settings.peer_id)
      if peer is None:  # pragma: no cover - database upsert invariant
        raise RuntimeError("Peer self-registration did not persist")
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
  def get(cls, peer: PeerRef) -> PeerModel | None:
    with SessionLocal() as db:
      return db.get(PeerModel, peer)

  @classmethod
  def get_all(cls) -> tuple[PeerModel, ...]:
    with SessionLocal() as db:
      return tuple(db.exec(sqlmodel.select(PeerModel)).all())

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
  def publish_self(cls) -> PeerModel:
    """Replace this Peer-owned capability snapshot from current config/registry."""
    with SessionLocal() as db:
      statement = (
        sqlmodel.select(PeerModel).where(PeerModel.id == settings.peer_id).with_for_update()
      )
      peer = db.exec(statement).one_or_none()
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
        typing.cast(
          dict[str, JSONValue],
          advertisement.model_dump(mode="json"),
        )
        for advertisement in advertisements
      ]
      if peer.capabilities != normalized:
        peer.capabilities = normalized
        db.add(peer)
        db.commit()
        db.refresh(peer)
      return peer

  @classmethod
  def renew_self_lease(cls, ttl_seconds: int) -> datetime.datetime:
    """Renew only liveness through the database-time SECURITY INVOKER helper."""
    if ttl_seconds <= 0:
      raise ValueError("Peer lease TTL must be positive")
    with SessionLocal() as db:
      expiry = db.exec(
        sqlmodel.select(
          getattr(sqlalchemy.func, PROTOCOL_SCHEMA).renew_peer_lease(
            settings.peer_id,
            ttl_seconds,
          )
        )
      ).one()
      db.commit()
      return typing.cast(datetime.datetime, expiry)

  @classmethod
  def refresh_self(cls, ttl_seconds: int) -> PeerModel:
    """Refresh advertisement from persisted config, then renew its route lease."""
    peer = cls.publish_self()
    peer.lease_expires_at = cls.renew_self_lease(ttl_seconds)
    return peer

  @classmethod
  def clear_self_lease(cls) -> None:
    with SessionLocal() as db:
      peer = db.get(PeerModel, settings.peer_id)
      if peer is None or peer.lease_expires_at is None:
        return
      peer.lease_expires_at = None
      db.add(peer)
      db.commit()

  @classmethod
  async def delegate(
    cls,
    capability: CapabilityID,
    payload: JSONValue,
    *,
    route_to_peer: PeerRef | None = None,
  ) -> JSONValue:
    """Execute through one eligible Peer, failing over only after non-execution."""
    candidates = cls._candidates(capability, route_to_peer)
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
  def _candidates(
    cls,
    capability: CapabilityID,
    route_to_peer: PeerRef | None,
  ) -> tuple[_Candidate, ...]:
    with SessionLocal() as db:
      statement = sqlmodel.select(PeerModel).where(
        PeerModel.id != settings.peer_id,
        PeerModel.lease_expires_at > sqlalchemy.func.statement_timestamp(),
      )
      if route_to_peer is not None:
        statement = statement.where(PeerModel.id == route_to_peer)
      peers = tuple(db.exec(statement).all())

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
