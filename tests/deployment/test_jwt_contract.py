"""Canonical JWT vectors shared conceptually by FastAPI and PostgREST."""

import jwt
import pytest

from app.database_contract.constants import (
  JWT_ALGORITHM,
  JWT_AUDIENCE,
  JWT_ISSUER,
  JWT_MAX_LIFETIME_SECONDS,
  JWT_ROLE,
)
from app.middleware import decode_peer_jwt


SECRET = "test-only-jwt-secret-at-least-32-bytes"  # noqa: S105
WRONG_SECRET = "wrong-test-jwt-secret-at-least-32-bytes"  # noqa: S105
NOW = 2_000_000_000


def _claims(**overrides):
  claims = {
    "role": JWT_ROLE,
    "iss": JWT_ISSUER,
    "aud": JWT_AUDIENCE,
    "iat": NOW,
    "exp": NOW + 600,
  }
  claims.update(overrides)
  return claims


def _encode(claims, secret=SECRET):
  return jwt.encode(claims, secret, algorithm=JWT_ALGORITHM)


def test_canonical_peer_jwt_is_accepted():
  token = _encode(_claims())

  assert decode_peer_jwt(token, SECRET, now=NOW)["role"] == JWT_ROLE


@pytest.mark.parametrize(
  "claims",
  [
    _claims(role="other"),
    _claims(iss="other"),
    _claims(aud="other"),
    _claims(iat=NOW + 61),
    _claims(exp=NOW),
    _claims(exp=NOW - 1),
    _claims(exp=NOW + JWT_MAX_LIFETIME_SECONDS + 1),
    _claims(iat="2000000000"),
    _claims(exp="2000000600"),
  ],
)
def test_peer_jwt_claim_drift_is_rejected(claims):
  with pytest.raises(jwt.exceptions.InvalidTokenError):
    decode_peer_jwt(_encode(claims), SECRET, now=NOW)


@pytest.mark.parametrize("missing", ["role", "iss", "aud", "iat", "exp"])
def test_peer_jwt_requires_every_canonical_claim(missing):
  claims = _claims()
  del claims[missing]

  with pytest.raises(jwt.exceptions.InvalidTokenError):
    decode_peer_jwt(_encode(claims), SECRET, now=NOW)


def test_peer_jwt_rejects_wrong_secret():
  with pytest.raises(jwt.exceptions.InvalidTokenError):
    decode_peer_jwt(_encode(_claims(), WRONG_SECRET), SECRET, now=NOW)
