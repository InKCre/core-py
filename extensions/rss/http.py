"""Bounded HTTP mechanics for feed snapshots and enrichment inputs."""

from __future__ import annotations

import dataclasses

import aiohttp

from utils.base import AIOHTTP_CONNECTOR_GETTER


READ_CHUNK_BYTES = 64 * 1024


class ResponseBodyTooLargeError(ValueError):
  """An HTTP response exceeded the caller-owned byte boundary."""


@dataclasses.dataclass(frozen=True)
class HTTPBytesResponse:
  status: int
  body: bytes
  effective_url: str
  etag: str | None
  last_modified: str | None
  content_type: str | None
  headers: dict[str, str]


@dataclasses.dataclass(frozen=True)
class HTTPFetchOptions:
  timeout_seconds: int
  max_response_bytes: int
  user_agent: str


async def fetch_http_bytes(
  url: str,
  *,
  options: HTTPFetchOptions,
  etag: str | None = None,
  last_modified: str | None = None,
) -> HTTPBytesResponse:
  """Fetch one HTTP(S) resource with conditional and byte-limit mechanics."""
  headers = {"User-Agent": options.user_agent}
  if etag:
    headers["If-None-Match"] = etag
  if last_modified:
    headers["If-Modified-Since"] = last_modified

  timeout = aiohttp.ClientTimeout(total=options.timeout_seconds)
  async with aiohttp.ClientSession(
    connector=AIOHTTP_CONNECTOR_GETTER(),
    timeout=timeout,
    headers=headers,
  ) as session:
    async with session.get(url, allow_redirects=True) as response:
      if response.status == 304:
        return HTTPBytesResponse(
          status=304,
          body=b"",
          effective_url=str(response.url),
          etag=response.headers.get("ETag") or etag,
          last_modified=response.headers.get("Last-Modified") or last_modified,
          content_type=response.headers.get("Content-Type"),
          headers={key.lower(): value for key, value in response.headers.items()},
        )
      response.raise_for_status()
      declared_length = response.content_length
      if declared_length is not None and declared_length > options.max_response_bytes:
        raise ResponseBodyTooLargeError(
          f"HTTP response declares {declared_length} bytes; "
          f"limit is {options.max_response_bytes}"
        )

      chunks: list[bytes] = []
      received = 0
      async for chunk in response.content.iter_chunked(READ_CHUNK_BYTES):
        received += len(chunk)
        if received > options.max_response_bytes:
          raise ResponseBodyTooLargeError(
            f"HTTP response exceeded {options.max_response_bytes} bytes"
          )
        chunks.append(chunk)

      return HTTPBytesResponse(
        status=response.status,
        body=b"".join(chunks),
        effective_url=str(response.url),
        etag=response.headers.get("ETag"),
        last_modified=response.headers.get("Last-Modified"),
        content_type=response.headers.get("Content-Type"),
        headers={key.lower(): value for key, value in response.headers.items()},
      )


__all__ = [
  "HTTPBytesResponse",
  "HTTPFetchOptions",
  "ResponseBodyTooLargeError",
  "fetch_http_bytes",
]
