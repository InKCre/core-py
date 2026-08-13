"""Stable and isolated PR-preview JWT signing identity."""

import pytest

from scripts.derive_preview_jwt_secret import derive_preview_jwt_secret


SEED = "preview-root-seed-with-at-least-thirty-two-bytes"


def test_derivation_is_stable_and_scoped_by_repository_and_pr():
  first = derive_preview_jwt_secret(SEED, "InKCre/core-py", 52)

  assert first == derive_preview_jwt_secret(SEED, "InKCre/core-py", 52)
  assert first != derive_preview_jwt_secret(SEED, "InKCre/core-py", 53)
  assert first != derive_preview_jwt_secret(SEED, "InKCre/client-web", 52)
  assert len(first) == 64


@pytest.mark.parametrize(
  ("seed", "repository", "pr_number"),
  [
    ("short", "InKCre/core-py", 52),
    (SEED, "core-py", 52),
    (SEED, "InKCre/core-py", 0),
  ],
)
def test_derivation_rejects_ambiguous_identity(
  seed: str,
  repository: str,
  pr_number: int,
):
  with pytest.raises(ValueError):
    derive_preview_jwt_secret(seed, repository, pr_number)
