"""Test-only composition helper for Extension-owned HTTP surfaces."""

from dataclasses import dataclass
import typing

import fastapi
from fastapi.testclient import TestClient

from app.business.extension import ExtensionBase
from app.business.extension.runtime import ExtensionRuntimeRecord


@dataclass
class PublishedExtension:
  app: fastapi.FastAPI
  extension: type[ExtensionBase]
  client: TestClient

  def unpublish(self) -> None:
    self.extension.unpublish()
    self.extension.release_runtime()


def publish_extension(
  extension: type[ExtensionBase],
  config: dict[str, typing.Any] | None = None,
  *,
  app: fastapi.FastAPI | None = None,
  raise_server_exceptions: bool = True,
) -> PublishedExtension:
  runtime_app = app or fastapi.FastAPI()
  runtime_config = dict(config or {})
  runtime_state: dict[str, typing.Any] = {}

  def persist_config(value: dict[str, typing.Any]) -> None:
    runtime_config.clear()
    runtime_config.update(value)

  def mutate_state(transform):
    next_state = transform(dict(runtime_state))
    runtime_state.clear()
    runtime_state.update(next_state)
    return dict(runtime_state)

  def mutate_config_and_state(transform):
    next_config, next_state = transform(dict(runtime_config), dict(runtime_state))
    runtime_config.clear()
    runtime_config.update(next_config)
    runtime_state.clear()
    runtime_state.update(next_state)
    return dict(runtime_config), dict(runtime_state)

  extension.unpublish()
  extension.release_runtime()
  extension.on_start(
    runtime_app,
    ExtensionRuntimeRecord(
      extension_id=extension.__extid__,
      config=dict(runtime_config),
      read_config=lambda: dict(runtime_config),
      persist_config=persist_config,
      read_state=lambda: dict(runtime_state),
      mutate_state=mutate_state,
      mutate_config_and_state=mutate_config_and_state,
      persist_config_schema=lambda _schema: None,
    ),
  )
  return PublishedExtension(
    runtime_app,
    extension,
    TestClient(runtime_app, raise_server_exceptions=raise_server_exceptions),
  )
