"""Deployment projection contract for a core Peer's public HTTP inbounds."""

from pathlib import Path

from scripts.configure_peer_runtime import (
  expected_capability_snapshot,
  snapshot_is_ready,
)


REPOSITORY_ROOT = Path(__file__).parents[2]


def test_expected_snapshot_is_exact_and_normalizes_base_url():
  snapshot = expected_capability_snapshot("https://core.example.test/")
  assert [item["id"] for item in snapshot] == [
    "core.extension.management.v1",
    "core.feature_retrieval.lexical.v1",
    "core.organization.rumination.v1",
    "core.semantic_retrieval.v1",
  ]
  assert [item["inbound"]["parameters"]["url"] for item in snapshot] == [
    "https://core.example.test/extension-management",
    "https://core.example.test/lexical-retrieval",
    "https://core.example.test/organization/ruminate",
    "https://core.example.test/semantic-retrieval",
  ]
  assert snapshot_is_ready(snapshot, True, snapshot)
  assert not snapshot_is_ready(snapshot, False, snapshot)
  assert not snapshot_is_ready(snapshot[:-1], True, snapshot)


def test_delivery_actions_use_peer_identity_and_database_config_projection():
  paths = (
    REPOSITORY_ROOT / ".github/actions/preview-delivery/action.yml",
    REPOSITORY_ROOT / ".github/actions/production-delivery/action.yml",
  )
  for path in paths:
    content = path.read_text(encoding="utf-8")
    assert "PEER_ID" in content
    assert "PEER_NAME" in content
    assert "configure_peer_runtime.py" in content
    assert '"CLIENT_ID=' not in content
    assert '"CLIENT_NAME=' not in content
    assert '"CLIENT_BASE_URL=' not in content
    assert "inputs.llm_sp_" not in content
    assert '"LLM_SP_AK=' not in content
    assert '"LLM_SP_BASE_URL=' not in content
