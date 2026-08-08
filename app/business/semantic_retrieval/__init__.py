"""Profile-scoped local semantic retrieval and embedding maintenance."""

from .main import (
  EmbeddingProfileNotFoundError,
  InvalidSemanticVectorError,
  SEMANTIC_RETRIEVAL_CONFIG_KEY,
  SEMANTIC_RETRIEVAL_CONFIG_SCHEMA,
  SEMANTIC_RETRIEVAL_CAPABILITY,
  SemanticRetrievalDelegationError,
  SemanticRetrievalError,
  SemanticRetrievalManager,
  SemanticRetrievalNotConfiguredError,
)

__all__ = [
  "EmbeddingProfileNotFoundError",
  "InvalidSemanticVectorError",
  "SEMANTIC_RETRIEVAL_CONFIG_KEY",
  "SEMANTIC_RETRIEVAL_CONFIG_SCHEMA",
  "SEMANTIC_RETRIEVAL_CAPABILITY",
  "SemanticRetrievalDelegationError",
  "SemanticRetrievalError",
  "SemanticRetrievalManager",
  "SemanticRetrievalNotConfiguredError",
]
