"""Test-only composition helper for Extension-owned HTTP surfaces."""

from dataclasses import dataclass
import typing

import fastapi
from fastapi.testclient import TestClient

from app.business.extension import ExtensionBase


@dataclass
class _TestActiveModel:
  name: str
  config: dict[str, typing.Any]
  state: dict[str, typing.Any]

  def update_config(self, value):
    self.config = dict(value)
    return self

  def update_config_schema(self, _schema):
    return self

  def read_state(self):
    return dict(self.state)

  def mutate_state(self, transform):
    self.state = transform(dict(self.state))
    return dict(self.state)

  def mutate_config_and_state(self, transform):
    self.config, self.state = transform(dict(self.config), dict(self.state))
    return dict(self.config), dict(self.state)


@dataclass
class PublishedExtension:
  app: fastapi.FastAPI
  extension: type[ExtensionBase]
  client: TestClient

  def unpublish(self) -> None:
    self.extension.unpublish()
    self.extension.unbind()
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

  extension.unpublish()
  extension.unbind()
  extension.release_runtime()
  extension.bind(
    _TestActiveModel(
      name=f"inkcre/{extension.__extid__}",
      config=runtime_config,
      state=runtime_state,
    )
  )
  extension.on_start(runtime_app)
  return PublishedExtension(
    runtime_app,
    extension,
    TestClient(runtime_app, raise_server_exceptions=raise_server_exceptions),
  )
