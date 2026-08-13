"""Canonical Core Extension Host management API."""

import typing

import fastapi
import pydantic

from app.business.extension import EXTENSION_HOST, InstalledExtension
from app.business.extension.errors import (
  ExtensionAcquisitionError,
  ExtensionCompatibilityError,
  ExtensionEntryPointError,
  ExtensionHostError,
  ExtensionNotInstalledError,
  ExtensionRegistryError,
  ExtensionRuntimeError,
  ExtensionStateConflictError,
)


ROUTER = fastapi.APIRouter(prefix="/extensions", tags=["extension"])


def _coordinate(namespace: str, name: str) -> str:
  return f"{namespace}/{name}"


def _raise_http_error(error: ExtensionHostError) -> typing.NoReturn:
  if isinstance(error, ExtensionNotInstalledError):
    status_code = fastapi.status.HTTP_404_NOT_FOUND
  elif isinstance(error, ExtensionRegistryError):
    status_code = fastapi.status.HTTP_502_BAD_GATEWAY
  elif isinstance(
    error,
    (
      ExtensionAcquisitionError,
      ExtensionCompatibilityError,
      ExtensionEntryPointError,
      ExtensionRuntimeError,
      ExtensionStateConflictError,
    ),
  ):
    status_code = fastapi.status.HTTP_409_CONFLICT
  else:
    status_code = fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR
  raise fastapi.HTTPException(status_code=status_code, detail=str(error)) from error


@ROUTER.get("")
def list_extensions() -> tuple[InstalledExtension, ...]:
  return EXTENSION_HOST.list()


@ROUTER.get("/{namespace}/{name}")
def get_extension(namespace: str, name: str) -> InstalledExtension:
  try:
    return EXTENSION_HOST.get(_coordinate(namespace, name))
  except ExtensionHostError as error:
    _raise_http_error(error)


@ROUTER.post("/{namespace}/{name}")
def install_extension(
  namespace: str,
  name: str,
  version: str = fastapi.Query(...),
) -> InstalledExtension:
  """Install one exact published Extension Release with no enabled peers."""
  try:
    return EXTENSION_HOST.install(_coordinate(namespace, name), version)
  except ExtensionHostError as error:
    _raise_http_error(error)


@ROUTER.delete("/{namespace}/{name}", status_code=204)
def uninstall_extension(namespace: str, name: str) -> fastapi.Response:
  try:
    EXTENSION_HOST.uninstall(_coordinate(namespace, name))
  except ExtensionHostError as error:
    _raise_http_error(error)
  return fastapi.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)


@ROUTER.put("/{namespace}/{name}/config")
def update_extension_config(
  namespace: str,
  name: str,
  body: dict[str, typing.Any] = fastapi.Body(...),
) -> InstalledExtension:
  try:
    return EXTENSION_HOST.update_config(_coordinate(namespace, name), body)
  except pydantic.ValidationError as error:
    raise fastapi.HTTPException(
      status_code=fastapi.status.HTTP_422_UNPROCESSABLE_CONTENT,
      detail=error.errors(include_url=False, include_context=False),
    ) from error
  except ExtensionHostError as error:
    _raise_http_error(error)


@ROUTER.post("/{namespace}/{name}/enable")
async def enable_extension(namespace: str, name: str) -> InstalledExtension:
  try:
    return await EXTENSION_HOST.enable(_coordinate(namespace, name))
  except ExtensionHostError as error:
    _raise_http_error(error)


@ROUTER.post("/{namespace}/{name}/disable")
async def disable_extension(namespace: str, name: str) -> InstalledExtension:
  try:
    return await EXTENSION_HOST.disable(_coordinate(namespace, name))
  except ExtensionHostError as error:
    _raise_http_error(error)
