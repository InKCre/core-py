"""Checked-in deployment profiles remain non-secret contract projections."""

import json
from pathlib import Path
from typing import Any, cast
import uuid
from urllib.parse import urlparse

from app.database_contract import (
  AUTHENTICATOR_ROLE,
  CONTRACT_REVISION,
  PROTOCOL_SCHEMA,
)
from app.database_contract.lifecycle import contract_document

PRODUCTION_PROFILE = Path(__file__).resolve().parents[2] / "deploy/profiles/production.json"


def test_production_profile_projects_the_executable_contract():
  profile = json.loads(PRODUCTION_PROFILE.read_text())
  contract = contract_document()

  assert profile["format"] == 1
  assert profile["environment"] == "production"
  assert contract["migration_heads"] == ["1e4c7a9b2d5f"]
  assert profile["database_contract"] == {
    "migration_head": "1e4c7a9b2d5f",
    "protocol_schema": PROTOCOL_SCHEMA,
    "revision": CONTRACT_REVISION,
  }
  assert profile["jwt"] == contract["jwt"]
  assert profile["postgrest"]["database_role"] == AUTHENTICATOR_ROLE
  assert profile["postgrest"]["anonymous_access"] == "deny"


def test_contract_publishes_the_complete_protocol_projection():
  contract = contract_document()
  protocol = cast(dict[str, Any], contract["protocol"])

  assert protocol["format"] == 1
  assert protocol["schema"] == PROTOCOL_SCHEMA
  assert set(protocol["relations"]) == {
    "agents",
    "ai_dialects",
    "ai_models",
    "ai_providers",
    "block_embeddings",
    "block_lexical_records",
    "blocks",
    "peers",
    "configs",
    "extensions",
    "embedding_profiles",
    "crons",
    "jobs",
    "job_types",
    "logs",
    "relation_embeddings",
    "relations",
    "sources",
    "sources_types",
    "storage_types",
    "storage_blobs",
    "storages",
  }
  assert protocol["functions"] == {
    "create_storage_blob": {
      "arguments": [
        {
          "name": None,
          "type": {"kind": "string", "format": "bytea"},
        }
      ],
      "returns": {"kind": "string", "format": "uuid"},
      "returns_set": False,
      "volatility": "volatile",
      "request_media_type": "application/octet-stream",
    },
    "read_storage_blob": {
      "arguments": [
        {
          "name": "blob_id",
          "type": {"kind": "string", "format": "uuid"},
        }
      ],
      "returns": {
        "kind": "string",
        "format": "bytea",
        "database_type": 'inkcre."application/octet-stream"',
      },
      "returns_set": False,
      "volatility": "stable",
      "response_media_type": "application/octet-stream",
    },
    "renew_peer_lease": {
      "arguments": [
        {
          "name": "peer",
          "type": {"kind": "string", "format": "uuid"},
        },
        {
          "name": "ttl_seconds",
          "type": {"kind": "number", "format": "integer"},
        },
      ],
      "returns": {
        "kind": "string",
        "format": "date-time",
        "database_type": "timestamp with time zone",
      },
      "returns_set": False,
      "volatility": "volatile",
    },
  }
  assert protocol["relations"]["peers"]["columns"]["id"] == {
    "type": {"kind": "string", "format": "uuid"},
    "nullable": False,
    "generated": False,
    "has_default": True,
  }
  assert protocol["relations"]["jobs"]["columns"]["status"]["type"] == {
    "kind": "enum",
    "values": ["pending", "running", "finished", "failed", "timed_out", "aborted"],
  }
  assert protocol["relations"]["block_embeddings"]["columns"]["embedding"]["type"] == {
    "kind": "array",
    "items": {"kind": "number"},
  }
  assert protocol["relations"]["block_lexical_records"]["columns"]["search_vector"][
    "type"
  ] == {"kind": "string", "format": "tsvector"}
  assert protocol["relations"]["storage_blobs"]["columns"]["data"]["type"] == {
    "kind": "string",
    "format": "bytea",
  }


def test_production_profile_has_stable_ids_and_https_endpoints():
  profile = json.loads(PRODUCTION_PROFILE.read_text())

  assert uuid.UUID(profile["peer"]["id"]).version == 4
  assert uuid.UUID(profile["core"]["peer_id"]).version == 5
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
