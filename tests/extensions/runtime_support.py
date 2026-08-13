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
  extension.unpublish()
  extension.release_runtime()
  extension.on_start(
    runtime_app,
    ExtensionRuntimeRecord(
      extension_id=extension.__extid__,
      config=config or {},
      persist_config=lambda _config: None,
      persist_config_schema=lambda _schema: None,
    ),
  )
  return PublishedExtension(
    runtime_app,
    extension,
    TestClient(runtime_app, raise_server_exceptions=raise_server_exceptions),
  )
