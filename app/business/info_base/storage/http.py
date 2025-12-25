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
import base64
import sqlmodel
from app.schemas.info_base.block import BlockModel
from .main import Storage
from utils.base import AIOHTTP_CONNECTOR_GETTER


class HTTPStorageConfig(sqlmodel.SQLModel):
  """Configuration for HTTP storage."""

  timeout: int = 30
  """Request timeout in seconds."""

  follow_redirects: bool = True
  """Whether to follow HTTP redirects."""


class HTTPStorage(Storage, config_cls=HTTPStorageConfig):
  """Base HTTP storage for fetching content from remote URLs.

  This storage type fetches content from HTTP/HTTPS URLs.
  Subclasses define how the content is processed and returned.
  """

  async def _fetch_url(self, url: str) -> aiohttp.ClientResponse:
    """Fetch a URL and return the response object."""
    config = self.get_config()
    async with aiohttp.ClientSession(
      connector=AIOHTTP_CONNECTOR_GETTER(),
      timeout=aiohttp.ClientTimeout(total=config.timeout),
    ) as session:
      async with session.get(url, allow_redirects=config.follow_redirects) as response:
        response.raise_for_status()
        return response

  async def get_content(self, block: BlockModel) -> str | bytes:
    """Fetch content from the URL in block.content.

    :param block: Block containing the URL in its content field
    :return: Content fetched from the URL
    """
    raise NotImplementedError("Subclasses must implement get_content")


class HTTPImageStorage(HTTPStorage):
  """HTTP storage for image content (returns base64-encoded data)."""

  async def get_content(self, block: BlockModel) -> str:
    """Fetch and encode image content as base64."""
    url = block.content
    config = self.get_config()
    async with aiohttp.ClientSession(
      connector=AIOHTTP_CONNECTOR_GETTER(),
      timeout=aiohttp.ClientTimeout(total=config.timeout),
    ) as session:
      async with session.get(url, allow_redirects=config.follow_redirects) as response:
        response.raise_for_status()
        content_bytes = await response.read()
        return base64.b64encode(content_bytes).decode("utf-8")


class HTTPVideoStorage(HTTPStorage):
  """HTTP storage for video content (returns raw bytes)."""

  async def get_content(self, block: BlockModel) -> bytes:
    """Fetch video content as bytes."""
    url = block.content
    config = self.get_config()
    async with aiohttp.ClientSession(
      connector=AIOHTTP_CONNECTOR_GETTER(),
      timeout=aiohttp.ClientTimeout(total=config.timeout),
    ) as session:
      async with session.get(url, allow_redirects=config.follow_redirects) as response:
        response.raise_for_status()
        content_bytes = await response.read()
        return content_bytes


class HTTPTextStorage(HTTPStorage):
  """HTTP storage for plain text content."""

  async def get_content(self, block: BlockModel) -> str:
    """Fetch text content from URL."""
    url = block.content
    config = self.get_config()
    async with aiohttp.ClientSession(
      connector=AIOHTTP_CONNECTOR_GETTER(),
      timeout=aiohttp.ClientTimeout(total=config.timeout),
    ) as session:
      async with session.get(url, allow_redirects=config.follow_redirects) as response:
        response.raise_for_status()
        return await response.text()


class HTTPJsonStorage(HTTPStorage):
  """HTTP storage for JSON content."""

  async def get_content(self, block: BlockModel) -> str:
    """Fetch JSON content from URL."""
    url = block.content
    config = self.get_config()
    async with aiohttp.ClientSession(
      connector=AIOHTTP_CONNECTOR_GETTER(),
      timeout=aiohttp.ClientTimeout(total=config.timeout),
    ) as session:
      async with session.get(url, allow_redirects=config.follow_redirects) as response:
        response.raise_for_status()
        return await response.text()


class HTTPBinaryStorage(HTTPStorage):
  """HTTP storage for binary content (returns raw bytes)."""

  async def get_content(self, block: BlockModel) -> bytes:
    """Fetch binary content as bytes."""
    url = block.content
    config = self.get_config()
    async with aiohttp.ClientSession(
      connector=AIOHTTP_CONNECTOR_GETTER(),
      timeout=aiohttp.ClientTimeout(total=config.timeout),
    ) as session:
      async with session.get(url, allow_redirects=config.follow_redirects) as response:
        response.raise_for_status()
        content_bytes = await response.read()
        return content_bytes


class HTTPHtmlStorage(HTTPStorage):
  """HTTP storage for HTML content (returns raw bytes)."""

  async def get_content(self, block: BlockModel) -> bytes:
    """Fetch HTML content as bytes."""
    url = block.content
    config = self.get_config()
    async with aiohttp.ClientSession(
      connector=AIOHTTP_CONNECTOR_GETTER(),
      timeout=aiohttp.ClientTimeout(total=config.timeout),
    ) as session:
      async with session.get(url, allow_redirects=config.follow_redirects) as response:
        response.raise_for_status()
        return await response.read()
