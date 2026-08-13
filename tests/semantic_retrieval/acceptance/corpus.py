"""Acceptance-only corpus authority and ranking judgments."""

from __future__ import annotations

import hashlib
from pathlib import Path
import typing

import pydantic


CORPUS_DIRECTORY = Path(__file__).parent / "corpus"
MANIFEST_PATH = CORPUS_DIRECTORY / "manifest.json"


class DocumentEntry(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  artifact: str
  source_url: str
  retrieved_at: str
  sha256: str
  provenance: str
  provenance_url: str


class DerivedAlias(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  source: str
  approach: str
  relation: str


class QualityQuery(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  id: str
  query: str
  primary: tuple[str, ...]
  distractors: tuple[str, ...]
  must_outrank: tuple[str, ...] = ()


class CorpusManifest(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  version: typing.Literal[1]
  documents: dict[str, DocumentEntry]
  producer_inputs: dict[str, dict[str, str]]
  derived_aliases: dict[str, DerivedAlias]
  quality_queries: tuple[QualityQuery, ...]

  @pydantic.model_validator(mode="after")
  def references_known_aliases(self) -> typing.Self:
    aliases = set(self.documents) | set(self.producer_inputs) | set(self.derived_aliases)
    for derived, definition in self.derived_aliases.items():
      if definition.source not in aliases:
        raise ValueError(f"derived alias {derived!r} references an unknown source")
    for judgment in self.quality_queries:
      referenced = set(judgment.primary + judgment.distractors + judgment.must_outrank)
      unknown = referenced - aliases
      if unknown:
        raise ValueError(f"query {judgment.id!r} references unknown aliases: {unknown!r}")
      if not judgment.primary:
        raise ValueError(f"query {judgment.id!r} has no primary alias")
    return self


def load_manifest() -> CorpusManifest:
  return CorpusManifest.model_validate_json(MANIFEST_PATH.read_text(encoding="utf-8"))


def verify_document_digests(manifest: CorpusManifest) -> None:
  for document in manifest.documents.values():
    digest = hashlib.sha256((CORPUS_DIRECTORY / document.artifact).read_bytes()).hexdigest()
    if digest != document.sha256:
      raise AssertionError(
        f"corpus artifact {document.artifact!r} has digest {digest}, "
        f"expected {document.sha256}"
      )


def assert_quality_judgment(
  judgment: QualityQuery,
  aliases: dict[str, int],
  ranked_entities: tuple[tuple[str, int], ...],
) -> None:
  """Apply the approved top-three and explicit-distractor quality gate."""
  ranks = {identity: index for index, identity in enumerate(ranked_entities, start=1)}

  def block_rank(alias: str) -> int | None:
    identity = ("block", aliases[alias])
    return ranks.get(identity)

  primary_ranks = tuple(
    rank for alias in judgment.primary if (rank := block_rank(alias)) is not None
  )
  if not primary_ranks:
    raise AssertionError(f"query {judgment.id!r} has no primary in bounded retrieval")
  primary_rank = min(primary_ranks)
  if primary_rank > 3:
    raise AssertionError(
      f"query {judgment.id!r} has best primary at rank {primary_rank}, expected top three"
    )
  for alias in judgment.distractors + judgment.must_outrank:
    other_rank = block_rank(alias)
    if other_rank is None:
      continue
    if primary_rank >= other_rank:
      raise AssertionError(
        f"query {judgment.id!r} primary rank {primary_rank} does not outrank "
        f"{alias!r} at rank {other_rank}"
      )
