"""REST lifecycle, authentication and native JSON/binary/multipart decoding."""

import json
import time
from email import policy
from email.parser import BytesParser
from typing import Any, cast

import httpx
import jwt

from .connection import Connection
from .errors import CommandError


def decode(response: httpx.Response) -> Any:
    if response.status_code == 204:
        return None
    content_type = response.headers.get("content-type", "")
    if content_type.split(";", 1)[0].strip().lower() == "multipart/related":
        message = BytesParser(policy=policy.default).parsebytes(
            f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode() + response.content
        )
        parts = list(message.iter_parts())
        root = json.loads(cast(bytes, parts[0].get_payload(decode=True)))
        binaries = {
            str(part["Content-ID"]).strip("<>"): cast(bytes, part.get_payload(decode=True))
            for part in parts[1:]
        }
        value: Any = root["value"]
        for pointer, content_id in root["parts"].items():
            binary = binaries[content_id.removeprefix("cid:")]
            if pointer == "":
                value = binary
                continue
            keys = [key.replace("~1", "/").replace("~0", "~") for key in pointer[1:].split("/")]
            parent: Any = value
            for key in keys[:-1]:
                parent = parent[int(key)] if isinstance(parent, list) else parent[key]
            parent[int(keys[-1]) if isinstance(parent, list) else keys[-1]] = binary
        return value
    if content_type.split(";", 1)[0].strip().lower() == "application/octet-stream":
        return response.content
    return response.json()


class CoreRESTClient:
    def __init__(self, connection: Connection):
        self.connection = connection
        self.base_url = str(connection.base_url).rstrip("/")
        self.client = httpx.Client(timeout=30)

    def close(self) -> None:
        self.client.close()

    def build_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        authenticated: bool = True,
        timeout: float | None = None,
    ) -> httpx.Request:
        headers = {}
        if authenticated:
            issued = int(time.time()) - 5
            token = jwt.encode(
                {
                    "role": "authenticated",
                    "iss": "inkcre-peer",
                    "aud": "inkcre-api",
                    "iat": issued,
                    "exp": issued + 15 * 60,
                },
                self.connection.jwt_secret,
                algorithm="HS256",
            )
            headers["Authorization"] = f"Bearer {token}"
        kwargs: dict[str, Any] = {"headers": headers}
        if timeout is not None:
            kwargs["timeout"] = timeout
        if params:
            kwargs["params"] = {key: value for key, value in params.items() if value is not None}
        if body is not None:
            kwargs["json"] = body
        return self.client.build_request(method, self.base_url + path, **kwargs)

    @staticmethod
    def read_response(response: httpx.Response) -> Any:
        if response.is_error:
            try:
                payload = response.json()
                detail = payload.get("detail", payload) if isinstance(payload, dict) else payload
            except ValueError:
                detail = response.text
            raise CommandError(detail, status=response.status_code)
        try:
            return decode(response)
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise CommandError(
                f"无法解码 Core 响应: {error}", status=response.status_code
            ) from error

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        return self.read_response(self.client.send(self.build_request(method, path, **kwargs)))
