"""Regression tests for the built-in GitHub resolvers."""

import asyncio
from datetime import datetime, timezone

from app.schemas.info_base.block import BlockModel
from extensions.github.resolver import GithubRepoResolver, GithubUserResolver
from extensions.github.schema import GithubRepo, GithubUser


def test_github_repo_resolver_uses_validated_content():
  repo = GithubRepo(
    id=1,
    name="core-py",
    full_name="InKCre/core-py",
    description="Backend",
    html_url="https://github.com/InKCre/core-py",
    language="Python",
    topics=["agents", "knowledge"],
    created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
  )
  resolver = GithubRepoResolver(
    BlockModel(resolver="github_repo", content=repo.model_dump_json())
  )

  assert asyncio.run(resolver.get_text()) == "InKCre/core-py: Backend"
  assert asyncio.run(resolver.get_str_for_embedding()) == (
    "InKCre/core-py\nBackend\nLanguage: Python\nTopics: agents, knowledge"
  )


def test_github_user_resolver_implements_embedding_contract():
  user = GithubUser(
    id=1,
    login="Sir",
    name="Lan",
    html_url="https://github.com/Sir",
  )
  resolver = GithubUserResolver(
    BlockModel(resolver="github_user", content=user.model_dump_json())
  )

  assert asyncio.run(resolver.get_text()) == "Lan (@sir)"
  assert asyncio.run(resolver.get_str_for_embedding()) == "Lan (@sir)"
