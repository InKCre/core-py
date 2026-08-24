"""Canonical GitHub collection facts."""

from __future__ import annotations

import typing

import pydantic


class GitHubAccount(pydantic.BaseModel):
  """One canonical GitHub user or organization account."""

  model_config = pydantic.ConfigDict(extra="forbid")

  node_id: str
  database_id: int | None = None
  kind: typing.Literal["user", "organization"]
  login: str
  name: str | None = None
  url: str
  avatar_url: str | None = None


class GitHubRepository(pydantic.BaseModel):
  """Stable Repository identity and useful source-authored metadata."""

  model_config = pydantic.ConfigDict(extra="forbid")

  node_id: str
  database_id: int | None = None
  name_with_owner: str
  description: str | None = None
  url: str
  homepage_url: str | None = None
  primary_language: str | None = None
  topics: tuple[str, ...] = ()
  is_private: bool
  is_archived: bool


class GitHubList(pydantic.BaseModel):
  """One GitHub List independent of its current membership."""

  model_config = pydantic.ConfigDict(extra="forbid")

  node_id: str
  name: str
  description: str | None = None
  slug: str
  is_private: bool


class GitHubRepositoryFact(pydantic.BaseModel):
  """One Repository together with its current canonical owner."""

  model_config = pydantic.ConfigDict(extra="forbid")

  repository: GitHubRepository
  owner: GitHubAccount


class GitHubListFact(pydantic.BaseModel):
  """One List and the exact Repository identities visible in its snapshot."""

  model_config = pydantic.ConfigDict(extra="forbid")

  list: GitHubList
  repository_node_ids: tuple[str, ...] = ()


class GitHubSnapshot(pydantic.BaseModel):
  """One complete authenticated Stars and Lists observation."""

  model_config = pydantic.ConfigDict(extra="forbid")

  account: GitHubAccount
  repositories: tuple[GitHubRepositoryFact, ...] = ()
  starred_repository_node_ids: tuple[str, ...] = ()
  lists: tuple[GitHubListFact, ...] = ()


class GitHubSourceConfig(pydantic.BaseModel):
  """Credentials for one GitHub access context."""

  model_config = pydantic.ConfigDict(extra="forbid")

  github_token: str = pydantic.Field(min_length=1)


class GitHubSourceState(pydantic.BaseModel):
  """Stable external account binding accepted by one Source."""

  model_config = pydantic.ConfigDict(extra="forbid")

  account_node_id: str | None = None


__all__ = [
  "GitHubAccount",
  "GitHubList",
  "GitHubListFact",
  "GitHubRepository",
  "GitHubRepositoryFact",
  "GitHubSnapshot",
  "GitHubSourceConfig",
  "GitHubSourceState",
]
