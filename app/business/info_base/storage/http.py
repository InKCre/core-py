"""HTTP-based storage for fetching content from URLs."""

__all__ = [
  "HTTPStorageConfig",
  "HTTPStorage",
  "HTTPImageStorage",
  "HTTPVideoStorage",
  "HTTPTextStorage",
  "HTTPJsonStorage",
  "HTTPBinaryStorage",
  "HTTPHtmlStorage",
]

import aiohttp
import typing
import sqlmodel
from .main import Storage
from utils.base import AIOHTTP_CONNECTOR_GETTER


class HTTPStorageConfig(sqlmodel.SQLModel):
  """Configuration for HTTP storage."""

  timeout: int = 30
  """Request timeout in seconds."""

  follow_redirects: bool = True
  """Whether to follow HTTP redirects."""


ContentTV = typing.TypeVar("ContentTV")
ConfigTV = typing.TypeVar("ConfigTV", bound=HTTPStorageConfig)


class HTTPStorage(
  Storage[ConfigTV, ContentTV],
  typing.Generic[ConfigTV, ContentTV],
  stg_type="http",
  config_cls=HTTPStorageConfig,
):
  """Base HTTP storage for fetching content from remote URLs.

  This storage type fetches content from HTTP/HTTPS URLs.
  Subclasses provides better handling for specific content types.
  """

  async def _fetch_url(self, url: str, headers: dict) -> aiohttp.ClientResponse:
    """Fetch a URL and return the response object."""
    async with aiohttp.ClientSession(
      connector=AIOHTTP_CONNECTOR_GETTER(),
      timeout=aiohttp.ClientTimeout(total=self._config.timeout),
    ) as session:
      async with session.get(
        url, allow_redirects=self._config.follow_redirects, headers=headers
      ) as response:
        response.raise_for_status()
        return response


class HTTPImageStorage(
  HTTPStorage[HTTPStorageConfig, bytes], stg_type="http_image", config_cls=HTTPStorageConfig
):
  """HTTP storage for image content (returns base64-encoded data)."""

  async def get_raw_content(self, block_content: str):
    """Fetch image from URL."""
    url = block_content
    response = await self._fetch_url(url, headers={"Accept": "image/*"})
    return await response.read()


class HTTPVideoStorage(
  HTTPStorage[HTTPStorageConfig, bytes], stg_type="http_video", config_cls=HTTPStorageConfig
):
  """HTTP storage for video content (returns raw bytes)."""

  async def get_raw_content(self, block_content: str):
    """Fetch video as bytes."""
    url = block_content
    response = await self._fetch_url(url, headers={"Accept": "video/*"})
    return await response.read()


class HTTPTextStorage(
  HTTPStorage[HTTPStorageConfig, str], stg_type="http_text", config_cls=HTTPStorageConfig
):
  """HTTP storage for plain text content."""

  async def get_raw_content(self, block_content: str):
    """Fetch text from URL."""
    url = block_content
    response = await self._fetch_url(url, headers={"Accept": "text/plain"})
    return await response.text()


class HTTPJsonStorage(
  HTTPStorage[HTTPStorageConfig, str], stg_type="http_json", config_cls=HTTPStorageConfig
):
  """HTTP storage for JSON content."""

  async def get_raw_content(self, block_content: str):
    """Fetch JSON string from URL."""
    url = block_content
    response = await self._fetch_url(url, headers={"Accept": "application/json"})
    return str((await response.json()).strip())


class HTTPBinaryStorage(
  HTTPStorage[HTTPStorageConfig, bytes],
  stg_type="http_binary",
  config_cls=HTTPStorageConfig,
):
  """HTTP storage for binary content (returns raw bytes)."""

  async def get_raw_content(self, block_content: str):
    """Fetch binary from URL."""
    url = block_content
    response = await self._fetch_url(url, headers={"Accept": "application/octet-stream"})
    return await response.read()


class HTTPHtmlStorage(
  HTTPStorage[HTTPStorageConfig, str], stg_type="http_html", config_cls=HTTPStorageConfig
):
  """HTTP storage for HTML content (returns raw bytes)."""

  async def get_raw_content(self, block_content: str):
    """Fetch HTML from URL."""
    url = block_content
    response = await self._fetch_url(url, headers={"Accept": "text/html"})
    return await response.text()
