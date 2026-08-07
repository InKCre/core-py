"""Static proof that the readable corpus stays acceptance-owned."""

from pathlib import Path

import pytest

from .corpus import (
  QualityQuery,
  assert_quality_judgment,
  load_manifest,
  verify_document_digests,
)


REPOSITORY_ROOT = Path(__file__).parents[3]
PRODUCTION_ROOTS = (
  REPOSITORY_ROOT / "app",
  REPOSITORY_ROOT / "extensions",
  REPOSITORY_ROOT / "libs",
  REPOSITORY_ROOT / "migrations",
)


def test_manifest_is_self_consistent_and_pinned():
  manifest = load_manifest()
  verify_document_digests(manifest)
  query_ids = tuple(query.id for query in manifest.quality_queries)
  assert len(query_ids) == len(set(query_ids))


def test_symbolic_aliases_do_not_enter_production_surfaces():
  manifest = load_manifest()
  aliases = (
    tuple(manifest.documents)
    + tuple(manifest.producer_inputs)
    + tuple(manifest.derived_aliases)
  )
  polluted: list[str] = []
  for root in PRODUCTION_ROOTS:
    for path in root.rglob("*"):
      if not path.is_file() or "__pycache__" in path.parts:
        continue
      try:
        content = path.read_text(encoding="utf-8")
      except UnicodeDecodeError:
        continue
      for alias in aliases:
        if alias in content:
          polluted.append(f"{path.relative_to(REPOSITORY_ROOT)}: {alias}")
  assert polluted == []


def test_quality_judgment_treats_omitted_fresh_candidates_as_below_the_bound():
  judgment = QualityQuery(
    id="bounded-ranking",
    query="query",
    primary=("primary",),
    distractors=("distractor",),
  )
  aliases = {"primary": 1, "distractor": 2}

  assert_quality_judgment(judgment, aliases, (("block", 1),))

  with pytest.raises(AssertionError, match="no primary"):
    assert_quality_judgment(judgment, aliases, (("block", 2),))
