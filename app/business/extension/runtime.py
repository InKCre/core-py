"""Reversible publication primitives shared by legacy and Registry extensions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import threading
import typing

import fastapi

from app.business.info_base.resolver.main import Resolver, ResolverManager
from app.business.source.main import SourceBase, SourceManager
from app.schemas.info_base.block import ResolverType


class ExtensionRuntimeClaimConflictError(RuntimeError):
  """Raised when another manager already owns an Extension runtime ID."""


class ExtensionRuntimeClaim:
  """An atomic, process-local claim for one canonical Extension runtime ID."""

  _lock = threading.Lock()
  _owners: dict[str, object] = {}

  def __init__(self, extension_id: str, token: object) -> None:
    self.extension_id = extension_id
    self._token = token
    self._released = False

  @classmethod
  def acquire(cls, extension_id: str) -> ExtensionRuntimeClaim:
    token = object()
    with cls._lock:
      if extension_id in cls._owners:
        raise ExtensionRuntimeClaimConflictError(
          f"Extension runtime {extension_id} already owns the canonical module"
        )
      cls._owners[extension_id] = token
    return cls(extension_id, token)

  def release(self) -> None:
    """Release this exact claim; repeated cleanup is intentionally harmless."""
    if self._released:
      return
    with self._lock:
      if self._owners.get(self.extension_id) is self._token:
        self._owners.pop(self.extension_id)
      self._released = True


@dataclass(frozen=True)
class ExtensionRuntimeRecord:
  """The narrow deployment state an Extension class needs at runtime."""

  extension_id: str
  config: dict[str, typing.Any]
  persist_config: Callable[[dict[str, typing.Any]], None]
  persist_config_schema: Callable[[dict[str, typing.Any]], None]


@dataclass
class ExtensionPublication:
  """The observable side effects contributed by one Extension startup."""

  app: fastapi.FastAPI
  routes: tuple[typing.Any, ...]
  source_types_before: dict[str, type[SourceBase]]
  source_types_published: dict[str, type[SourceBase]]
  resolvers_before: dict[ResolverType, type[Resolver]]
  resolvers_published: dict[ResolverType, type[Resolver]]
  restored: bool = False

  def restore(self) -> None:
    """Withdraw this publication without disturbing unrelated later routes."""
    if self.restored:
      return

    route_ids = {id(route) for route in self.routes}
    self.app.router.routes[:] = [
      route for route in self.app.router.routes if id(route) not in route_ids
    ]
    SourceManager.restore_source_types(
      self.source_types_before,
      self.source_types_published,
    )
    ResolverManager.restore_resolvers(
      self.resolvers_before,
      self.resolvers_published,
    )
    self.app.openapi_schema = None
    self.restored = True


@dataclass(frozen=True)
class ExtensionPublicationSnapshot:
  """Before-state used to finalize or roll back one startup publication."""

  app: fastapi.FastAPI
  route_ids: frozenset[int]
  source_types: dict[str, type[SourceBase]]
  resolvers: dict[ResolverType, type[Resolver]]

  @classmethod
  def capture(cls, app: fastapi.FastAPI) -> ExtensionPublicationSnapshot:
    return cls(
      app=app,
      route_ids=frozenset(id(route) for route in app.router.routes),
      source_types=SourceManager.snapshot_source_types(),
      resolvers=ResolverManager.snapshot_resolvers(),
    )

  def finish(self) -> ExtensionPublication:
    publication = ExtensionPublication(
      app=self.app,
      routes=tuple(
        route for route in self.app.router.routes if id(route) not in self.route_ids
      ),
      source_types_before=self.source_types,
      source_types_published=SourceManager.snapshot_source_types(),
      resolvers_before=self.resolvers,
      resolvers_published=ResolverManager.snapshot_resolvers(),
    )
    self.app.openapi_schema = None
    return publication

  def rollback(self) -> None:
    self.finish().restore()
