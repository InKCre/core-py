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
    BlockModel(resolver=GithubRepoResolver.__rsotype__, content=repo.model_dump_json())
  )

  assert asyncio.run(resolver.get_text()) == (
    "InKCre/core-py\nBackend\nLanguage: Python\nTopics: agents, knowledge"
  )
  assert asyncio.run(resolver.get_label()) == "github repository <InKCre/core-py>"


def test_github_user_resolver_exposes_one_complete_text_projection():
  user = GithubUser(
    id=1,
    login="Sir",
    name="Lan",
    html_url="https://github.com/Sir",
  )
  resolver = GithubUserResolver(
    BlockModel(resolver=GithubUserResolver.__rsotype__, content=user.model_dump_json())
  )

  assert asyncio.run(resolver.get_text()) == "Lan (@sir)"
  assert asyncio.run(resolver.get_label()) == "github user <sir>"
