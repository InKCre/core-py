"""Same-response JSON/binary/MIME delivery for ordinary REST content reads."""

import json
import typing

import aiohttp
import fastapi
import pydantic
from pydantic_core import to_jsonable_python


_VALUE = pydantic.TypeAdapter(typing.Any)
CONTENT_RESPONSES: dict[int | str, dict[str, typing.Any]] = {
  200: {
    "content": {
      "application/json": {},
      "application/octet-stream": {},
      "multipart/related": {},
    }
  },
}


def _json_bytes(value: typing.Any) -> bytes:
  return json.dumps(
    value,
    ensure_ascii=False,
    separators=(",", ":"),
    allow_nan=False,
    default=to_jsonable_python,
  ).encode("utf-8")


async def content_response(value: typing.Any) -> fastapi.Response:
  """Keep bytes typed without reserving sentinel shapes in authored JSON.

  Multipart's first part contains {value, parts}: parts maps RFC 6901 pointers
  into value to binary Content-IDs. Only mapped nulls stand for bytes. No result
  cache or second Resolver call is involved; current producers already hold bytes
  in memory, so this adapter does not promise bounded-memory streaming.
  """
  value = _VALUE.dump_python(value, mode="python", by_alias=True)
  if isinstance(value, bytes):
    return fastapi.Response(value, media_type="application/octet-stream")
  blobs: list[tuple[str, bytes]] = []
  parts: dict[str, str] = {}

  def split(item: typing.Any, pointer: str) -> typing.Any:
    if isinstance(item, bytes):
      content_id = f"body-{len(blobs) + 1}@inkcre"
      parts[pointer] = content_id
      blobs.append((content_id, item))
      return None
    if isinstance(item, dict):
      return {
        str(key): split(
          child, pointer + "/" + str(key).replace("~", "~0").replace("/", "~1")
        )
        for key, child in item.items()
      }
    if isinstance(item, (list, tuple)):
      return [split(child, f"{pointer}/{index}") for index, child in enumerate(item)]
    return item

  projected = split(value, "")
  if not blobs:
    return fastapi.Response(_json_bytes(projected), media_type="application/json")
  writer = aiohttp.MultipartWriter("related")
  writer.append(
    _json_bytes({"value": projected, "parts": parts}),
    {
      "Content-Type": "application/json",
    },
  )
  for content_id, blob in blobs:
    writer.append(
      blob,
      {
        "Content-Type": "application/octet-stream",
        "Content-ID": f"<{content_id}>",
      },
    )
  return fastapi.Response(
    await writer.as_bytes(),
    headers={"Content-Type": writer.content_type + '; type="application/json"'},
  )
