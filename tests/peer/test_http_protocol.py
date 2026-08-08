"""Black-box core.peer.protocol.http.v1 outbound behavior."""

from __future__ import annotations

import asyncio
import typing
import uuid

import httpx
import jwt
import pytest

import app.business.peer.http as peer_http
from app.business.peer import PeerHTTPOutbound, PeerOutcomeUnknown, PeerRequestNotExecuted
from app.database_contract.constants import JWT_AUDIENCE, JWT_ISSUER, JWT_ROLE
from app.schemas.peer import PeerModel


def _peer() -> PeerModel:
  return PeerModel(id=uuid.uuid4(), name="remote")


class _AsyncClient:
  response: httpx.Response | Exception
  request_arguments: dict = {}

  def __init__(self, **_kwargs):
    pass

  async def __aenter__(self):
    return self

  async def __aexit__(self, *_args):
    return None

  async def request(self, **kwargs):
    type(self).request_arguments = kwargs
    if isinstance(type(self).response, Exception):
      raise typing.cast(Exception, type(self).response)
    return type(self).response


def test_http_outbound_preserves_query_body_and_peer_auth(monkeypatch):
  request = httpx.Request("POST", "https://provider.example/semantic-retrieval")
  _AsyncClient.response = httpx.Response(
    200,
    request=request,
    headers=[("X-Trace", "one"), ("X-Trace", "two")],
    json={"matches": []},
  )
  monkeypatch.setattr(peer_http.httpx, "AsyncClient", _AsyncClient)
  outbound = PeerHTTPOutbound(
    _peer(),
    {"method": "post", "url": str(request.url)},
  )

  result = asyncio.run(
    outbound.execute(
      {
        "query": {"trace": ["compact"]},
        "headers": {"x-domain": ["semantic"]},
        "body": {"query": "graph"},
      }
    )
  )

  arguments = _AsyncClient.request_arguments
  assert arguments["params"] == [("trace", "compact")]
  assert arguments["json"] == {"query": "graph"}
  assert ("x-domain", "semantic") in arguments["headers"]
  token = dict(arguments["headers"])["authorization"].removeprefix("Bearer ")
  claims = jwt.decode(
    token,
    peer_http.settings.jwt_secret,
    algorithms=["HS256"],
    audience=JWT_AUDIENCE,
    issuer=JWT_ISSUER,
  )
  assert claims["role"] == JWT_ROLE
  assert result == {
    "status": 200,
    "headers": {
      "content-length": ["14"],
      "content-type": ["application/json"],
      "x-trace": ["one", "two"],
    },
    "body": {"matches": []},
  }


def test_http_outbound_preserves_empty_204(monkeypatch):
  request = httpx.Request("POST", "https://provider.example/organization/ruminate")
  _AsyncClient.response = httpx.Response(204, request=request)
  monkeypatch.setattr(peer_http.httpx, "AsyncClient", _AsyncClient)

  result = asyncio.run(
    PeerHTTPOutbound(
      _peer(),
      {"method": "POST", "url": str(request.url)},
    ).execute({"body": {"block": 1}})
  )

  assert result == {"status": 204, "headers": {}}


def test_http_outbound_uses_exact_non_execution_proof(monkeypatch):
  request = httpx.Request("POST", "https://provider.example/organization/ruminate")
  _AsyncClient.response = httpx.Response(
    503,
    request=request,
    headers={"InkCre-Peer-Execution": "not-executed"},
  )
  monkeypatch.setattr(peer_http.httpx, "AsyncClient", _AsyncClient)

  with pytest.raises(PeerRequestNotExecuted):
    asyncio.run(
      PeerHTTPOutbound(
        _peer(),
        {"method": "POST", "url": str(request.url)},
      ).execute({})
    )


@pytest.mark.parametrize(
  ("failure", "expected"),
  [
    (
      httpx.ConnectError(
        "connect failed",
        request=httpx.Request("POST", "https://provider.example"),
      ),
      PeerRequestNotExecuted,
    ),
    (
      httpx.ReadTimeout(
        "response unknown",
        request=httpx.Request("POST", "https://provider.example"),
      ),
      PeerOutcomeUnknown,
    ),
  ],
)
def test_http_outbound_separates_pre_and_post_dispatch_failures(
  monkeypatch,
  failure,
  expected,
):
  _AsyncClient.response = failure
  monkeypatch.setattr(peer_http.httpx, "AsyncClient", _AsyncClient)

  with pytest.raises(expected):
    asyncio.run(
      PeerHTTPOutbound(
        _peer(),
        {"method": "POST", "url": "https://provider.example/action"},
      ).execute({})
    )
