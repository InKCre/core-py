"""Checked-in deployment profiles remain non-secret contract projections."""

import json
from pathlib import Path
import uuid
from urllib.parse import urlparse

from app.database_contract import (
  AUTHENTICATOR_ROLE,
  CONTRACT_REVISION,
  PROTOCOL_SCHEMA,
)
from app.database_contract.lifecycle import contract_document

PRODUCTION_PROFILE = Path(__file__).resolve().parents[1] / "deploy/profiles/production.json"


def test_production_profile_projects_the_executable_contract():
  profile = json.loads(PRODUCTION_PROFILE.read_text())
  contract = contract_document()

  assert profile["format"] == 1
  assert profile["environment"] == "production"
  assert profile["database_contract"] == {
    "migration_head": "d9f4e2a1b7c3",
    "protocol_schema": PROTOCOL_SCHEMA,
    "revision": CONTRACT_REVISION,
  }
  assert profile["jwt"] == contract["jwt"]
  assert profile["postgrest"]["database_role"] == AUTHENTICATOR_ROLE
  assert profile["postgrest"]["anonymous_access"] == "deny"


def test_production_profile_has_stable_ids_and_https_endpoints():
  profile = json.loads(PRODUCTION_PROFILE.read_text())

  assert uuid.UUID(profile["client"]["id"]).version == 4
  assert uuid.UUID(profile["core"]["client_id"]).version == 5
  for peer in ("core", "postgrest"):
    endpoint = urlparse(profile[peer]["url"])
    assert endpoint.scheme == "https"
    assert endpoint.hostname is not None
    assert endpoint.hostname.endswith(".herokuapp.com")
    assert endpoint.path == "/"


def test_production_profile_contains_no_secret_inputs():
  profile_text = PRODUCTION_PROFILE.read_text().lower()

  for forbidden in ("password", "jwt_secret", "database_url", "api_key", "token"):
    assert forbidden not in profile_text
