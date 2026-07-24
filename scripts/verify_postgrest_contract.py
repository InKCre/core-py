"""Black-box acceptance probe for the authenticated PostgREST peer contract."""

import argparse
import json
import time
from urllib import error, parse, request
import uuid

import jwt

from app.database_contract.constants import (
  JWT_ALGORITHM,
  JWT_AUDIENCE,
  JWT_ISSUER,
  JWT_ROLE,
)


PROBE_CLIENT_ID = uuid.UUID("00000000-0000-4000-8000-000000000099")


def _token(secret: str, *, now: int | None = None) -> str:
  issued_at = now if now is not None else int(time.time())
  return jwt.encode(
    {
      "role": JWT_ROLE,
      "iss": JWT_ISSUER,
      "aud": JWT_AUDIENCE,
      "iat": issued_at,
      "exp": issued_at + 600,
    },
    secret,
    algorithm=JWT_ALGORITHM,
  )


def _call(
  base_url: str,
  path: str,
  *,
  method: str = "GET",
  token: str | None = None,
  document: object | None = None,
) -> tuple[int, bytes]:
  headers = {"Accept": "application/json"}
  if token is not None:
    headers["Authorization"] = f"Bearer {token}"
  body = None
  if document is not None:
    headers["Content-Type"] = "application/json"
    headers["Prefer"] = "return=representation"
    body = json.dumps(document).encode()
  http_request = request.Request(
    f"{base_url.rstrip('/')}/{path.lstrip('/')}",
    data=body,
    headers=headers,
    method=method,
  )
  try:
    with request.urlopen(http_request, timeout=10) as response:
      return response.status, response.read()
  except error.HTTPError as exc:
    return exc.code, exc.read()


def _expect(actual: int, expected: int, name: str) -> None:
  if actual != expected:
    raise RuntimeError(f"{name} returned HTTP {actual}, expected {expected}")


def verify(base_url: str, secret: str, wrong_secret: str) -> dict[str, object]:
  """Prove representative read/write and rejection semantics."""
  valid_token = _token(secret)
  invalid_token = _token(wrong_secret)
  escaped_id = parse.quote(str(PROBE_CLIENT_ID), safe="")

  _call(
    base_url,
    f"clients?id=eq.{escaped_id}",
    method="DELETE",
    token=valid_token,
  )

  checks: dict[str, int] = {}
  checks["authenticated_read"], _ = _call(
    base_url,
    "clients?select=id&limit=1",
    token=valid_token,
  )
  _expect(checks["authenticated_read"], 200, "authenticated read")

  checks["authenticated_write"], response_body = _call(
    base_url,
    "clients",
    method="POST",
    token=valid_token,
    document={
      "id": str(PROBE_CLIENT_ID),
      "name": "postgrest-contract-probe",
      "labels": ["contract-probe"],
      "config": {},
      "config_schema": {},
    },
  )
  _expect(checks["authenticated_write"], 201, "authenticated write")
  created = json.loads(response_body)
  if not created or created[0].get("id") != str(PROBE_CLIENT_ID):
    raise RuntimeError("authenticated write returned an unexpected record")

  checks["wrong_secret"], _ = _call(
    base_url,
    "clients?select=id&limit=1",
    token=invalid_token,
  )
  _expect(checks["wrong_secret"], 401, "wrong secret")

  checks["anonymous"], _ = _call(
    base_url,
    "clients?select=id&limit=1",
  )
  _expect(checks["anonymous"], 401, "anonymous request")

  checks["cleanup"], _ = _call(
    base_url,
    f"clients?id=eq.{escaped_id}",
    method="DELETE",
    token=valid_token,
  )
  _expect(checks["cleanup"], 204, "probe cleanup")

  return {
    "status": "ok",
    "surface": "postgrest",
    "checks": checks,
  }


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser()
  parser.add_argument("--base-url", required=True)
  parser.add_argument("--jwt-secret", required=True)
  parser.add_argument("--wrong-jwt-secret", required=True)
  return parser


def main() -> int:
  args = build_parser().parse_args()
  try:
    result = verify(
      args.base_url,
      args.jwt_secret,
      args.wrong_jwt_secret,
    )
  except Exception:
    print(
      json.dumps(
        {
          "status": "error",
          "surface": "postgrest",
          "reason": "acceptance_failed",
        },
        sort_keys=True,
      )
    )
    return 1
  print(json.dumps(result, sort_keys=True))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
