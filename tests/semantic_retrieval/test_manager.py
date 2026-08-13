"""SemanticRetrievalManager default selection and vector guardrails."""

import pytest

from app.business.deployment_config import DeploymentConfigManager
from app.business.semantic_retrieval import (
  InvalidSemanticVectorError,
  SemanticRetrievalManager,
  SemanticRetrievalNotConfiguredError,
)
from app.schemas.semantic_retrieval import SemanticRetrievalConfig


def test_default_profile_distinguishes_missing_and_selected(monkeypatch):
  monkeypatch.setattr(
    DeploymentConfigManager,
    "get",
    classmethod(lambda _cls, _key: None),
  )
  with pytest.raises(SemanticRetrievalNotConfiguredError):
    SemanticRetrievalManager._configured_profile_id()

  monkeypatch.setattr(
    DeploymentConfigManager,
    "get",
    classmethod(lambda _cls, _key: SemanticRetrievalConfig(default_profile=42)),
  )
  assert SemanticRetrievalManager._configured_profile_id() == 42


def test_semantic_vectors_must_be_non_zero():
  with pytest.raises(InvalidSemanticVectorError):
    SemanticRetrievalManager._require_non_zero_vector((0.0, 0.0))
  SemanticRetrievalManager._require_non_zero_vector((0.0, 1.0))
