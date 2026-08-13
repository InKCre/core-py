"""Derive one stable, repository-qualified JWT secret for a PR preview."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import os
import re


REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


def derive_preview_jwt_secret(seed: str, repository: str, pr_number: int) -> str:
  """Return an isolated, reproducible HS256 key without exposing the root seed."""
  if len(seed.encode()) < 32:
    raise ValueError("PREVIEW_JWT_SEED must contain at least 32 bytes")
  if REPOSITORY_PATTERN.fullmatch(repository) is None:
    raise ValueError("repository must be an owner/name pair")
  if pr_number < 1:
    raise ValueError("PR number must be positive")

  context = f"inkcre-preview-jwt-v1\nrepository={repository}\npr={pr_number}\n"
  return hmac.new(seed.encode(), context.encode(), hashlib.sha256).hexdigest()


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("--repository", required=True)
  parser.add_argument("--pr-number", required=True, type=int)
  args = parser.parse_args()

  seed = os.environ.get("PREVIEW_JWT_SEED", "")
  print(derive_preview_jwt_secret(seed, args.repository, args.pr_number))


if __name__ == "__main__":
  main()
