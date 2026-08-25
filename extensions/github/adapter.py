"""Async GitHub GraphQL access without info-base dependencies."""

from __future__ import annotations

import typing

import httpx

from .schema import (
  GitHubAccount,
  GitHubList,
  GitHubListFact,
  GitHubRepository,
  GitHubRepositoryFact,
  GitHubSnapshot,
)


_REPOSITORY_FIELDS = """
  id
  databaseId
  nameWithOwner
  description
  url
  homepageUrl
  isPrivate
  isArchived
  primaryLanguage { name }
  repositoryTopics(first: 20) { nodes { topic { name } } }
  owner {
    __typename
    id
    login
    url
    avatarUrl
    ... on User { databaseId name }
    ... on Organization { databaseId name }
  }
"""

_ACCOUNT_AND_STARS_QUERY = f"""
query GitHubStars($cursor: String) {{
  viewer {{
    id
    databaseId
    login
    name
    url
    avatarUrl
    starredRepositories(first: 50, after: $cursor) {{
      nodes {{ {_REPOSITORY_FIELDS} }}
      pageInfo {{ hasNextPage endCursor }}
    }}
  }}
}}
"""

_LISTS_QUERY = f"""
query GitHubLists($cursor: String) {{
  viewer {{
    lists(first: 100, after: $cursor) {{
      nodes {{
        id
        name
        description
        slug
        isPrivate
        items(first: 100) {{
          nodes {{ ... on Repository {{ id }} }}
          pageInfo {{ hasNextPage endCursor }}
        }}
      }}
      pageInfo {{ hasNextPage endCursor }}
    }}
  }}
}}
"""

_LIST_ITEMS_QUERY = f"""
query GitHubListItems($id: ID!, $cursor: String) {{
  node(id: $id) {{
    ... on UserList {{
      items(first: 100, after: $cursor) {{
        nodes {{ ... on Repository {{ id }} }}
        pageInfo {{ hasNextPage endCursor }}
      }}
    }}
  }}
}}
"""

_REPOSITORIES_QUERY = f"""
query GitHubRepositories($ids: [ID!]!) {{
  nodes(ids: $ids) {{
    ... on Repository {{ {_REPOSITORY_FIELDS} }}
  }}
}}
"""


class GitHubGraphQLError(RuntimeError):
  """GitHub did not provide one complete valid GraphQL observation."""


def _object(value: typing.Any, context: str) -> dict[str, typing.Any]:
  if not isinstance(value, dict):
    raise GitHubGraphQLError(f"GitHub GraphQL omitted {context}")
  return value


def _page_info(connection: dict[str, typing.Any]) -> tuple[bool, str | None]:
  page = _object(connection.get("pageInfo"), "pageInfo")
  has_next = page.get("hasNextPage")
  cursor = page.get("endCursor")
  if not isinstance(has_next, bool):
    raise GitHubGraphQLError("GitHub GraphQL returned invalid pageInfo")
  if has_next and not isinstance(cursor, str):
    raise GitHubGraphQLError("GitHub GraphQL pagination omitted endCursor")
  return has_next, cursor if isinstance(cursor, str) else None


def _account(value: dict[str, typing.Any], *, viewer: bool = False) -> GitHubAccount:
  typename = "User" if viewer else value.get("__typename")
  if typename not in {"User", "Organization"}:
    raise GitHubGraphQLError("GitHub returned an unsupported account kind")
  return GitHubAccount.model_validate(
    {
      "node_id": value.get("id"),
      "database_id": value.get("databaseId"),
      "kind": "user" if typename == "User" else "organization",
      "login": value.get("login"),
      "name": value.get("name"),
      "url": value.get("url"),
      "avatar_url": value.get("avatarUrl"),
    }
  )


def _repository(value: dict[str, typing.Any]) -> GitHubRepositoryFact:
  owner = _object(value.get("owner"), "Repository.owner")
  language = value.get("primaryLanguage")
  topic_connection = _object(value.get("repositoryTopics"), "repositoryTopics")
  topic_nodes = topic_connection.get("nodes")
  if not isinstance(topic_nodes, list):
    raise GitHubGraphQLError("GitHub GraphQL returned invalid repository topics")
  topics = tuple(
    topic["topic"]["name"]
    for topic in topic_nodes
    if isinstance(topic, dict)
    and isinstance(topic.get("topic"), dict)
    and isinstance(topic["topic"].get("name"), str)
  )
  return GitHubRepositoryFact(
    repository=GitHubRepository.model_validate(
      {
        "node_id": value.get("id"),
        "database_id": value.get("databaseId"),
        "name_with_owner": value.get("nameWithOwner"),
        "description": value.get("description"),
        "url": value.get("url"),
        "homepage_url": value.get("homepageUrl"),
        "primary_language": (language.get("name") if isinstance(language, dict) else None),
        "topics": topics,
        "is_private": value.get("isPrivate"),
        "is_archived": value.get("isArchived"),
      }
    ),
    owner=_account(owner),
  )


class GitHubGraphQLAdapter:
  """Fetch one complete GitHub Stars/Lists snapshot."""

  def __init__(self, token: str, *, client: httpx.AsyncClient | None = None):
    self._owned_client = client is None
    self._client = client or httpx.AsyncClient(
      base_url="https://api.github.com",
      headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "InKCre-GitHub-Extension",
        "X-GitHub-Api-Version": "2022-11-28",
      },
      timeout=30,
    )

  async def __aenter__(self) -> "GitHubGraphQLAdapter":
    return self

  async def __aexit__(self, *_exc: object) -> None:
    if self._owned_client:
      await self._client.aclose()

  async def _execute(
    self,
    query: str,
    variables: dict[str, typing.Any],
  ) -> dict[str, typing.Any]:
    response = await self._client.post(
      "/graphql",
      json={"query": query, "variables": variables},
    )
    response.raise_for_status()
    payload = _object(response.json(), "response")
    errors = payload.get("errors")
    if errors:
      messages = [
        error.get("message", "unknown GraphQL error")
        for error in errors
        if isinstance(error, dict)
      ]
      raise GitHubGraphQLError("; ".join(messages) or "GitHub GraphQL request failed")
    return _object(payload.get("data"), "data")

  async def fetch_snapshot(self) -> GitHubSnapshot:
    repositories: dict[str, GitHubRepositoryFact] = {}
    starred_ids: list[str] = []
    account: GitHubAccount | None = None
    cursor: str | None = None

    while True:
      data = await self._execute(_ACCOUNT_AND_STARS_QUERY, {"cursor": cursor})
      viewer = _object(data.get("viewer"), "viewer")
      observed_account = _account(viewer, viewer=True)
      if account is not None and observed_account.node_id != account.node_id:
        raise GitHubGraphQLError("GitHub viewer changed during pagination")
      account = observed_account
      connection = _object(viewer.get("starredRepositories"), "starredRepositories")
      nodes = connection.get("nodes")
      if not isinstance(nodes, list):
        raise GitHubGraphQLError("GitHub GraphQL returned invalid starredRepositories")
      for node in nodes:
        fact = _repository(_object(node, "starred Repository"))
        repositories[fact.repository.node_id] = fact
        starred_ids.append(fact.repository.node_id)
      has_next, cursor = _page_info(connection)
      if not has_next:
        break

    lists: list[GitHubListFact] = []
    cursor = None
    while True:
      data = await self._execute(_LISTS_QUERY, {"cursor": cursor})
      viewer = _object(data.get("viewer"), "viewer")
      connection = _object(viewer.get("lists"), "viewer.lists")
      nodes = connection.get("nodes")
      if not isinstance(nodes, list):
        raise GitHubGraphQLError("GitHub GraphQL returned invalid Lists")
      for node_value in nodes:
        node = _object(node_value, "List")
        item_connection = _object(node.get("items"), "List.items")
        item_ids = self._collect_repository_ids(item_connection)
        has_more_items, item_cursor = _page_info(item_connection)
        while has_more_items:
          item_data = await self._execute(
            _LIST_ITEMS_QUERY,
            {"id": node.get("id"), "cursor": item_cursor},
          )
          list_node = _object(item_data.get("node"), "UserList node")
          item_connection = _object(list_node.get("items"), "List.items")
          item_ids.extend(self._collect_repository_ids(item_connection))
          has_more_items, item_cursor = _page_info(item_connection)
        lists.append(
          GitHubListFact(
            list=GitHubList.model_validate(
              {
                "node_id": node.get("id"),
                "name": node.get("name"),
                "description": node.get("description"),
                "slug": node.get("slug"),
                "is_private": node.get("isPrivate"),
              }
            ),
            repository_node_ids=tuple(dict.fromkeys(item_ids)),
          )
        )
      has_next, cursor = _page_info(connection)
      if not has_next:
        break

    if account is None:  # pragma: no cover - at least one Stars page is required
      raise GitHubGraphQLError("GitHub GraphQL omitted the authenticated account")
    unknown_memberships = {
      node_id
      for list_ in lists
      for node_id in list_.repository_node_ids
      if node_id not in repositories
    }
    missing_ids = sorted(unknown_memberships)
    for offset in range(0, len(missing_ids), 50):
      requested = missing_ids[offset : offset + 50]
      data = await self._execute(_REPOSITORIES_QUERY, {"ids": requested})
      nodes = data.get("nodes")
      if not isinstance(nodes, list):
        raise GitHubGraphQLError("GitHub GraphQL returned invalid Repository nodes")
      for node in nodes:
        fact = _repository(_object(node, "List-only Repository"))
        repositories[fact.repository.node_id] = fact
    unresolved = unknown_memberships - repositories.keys()
    if unresolved:
      raise GitHubGraphQLError("GitHub could not resolve every List Repository")
    return GitHubSnapshot(
      account=account,
      repositories=tuple(repositories.values()),
      starred_repository_node_ids=tuple(dict.fromkeys(starred_ids)),
      lists=tuple(lists),
    )

  @staticmethod
  def _collect_repository_ids(connection: dict[str, typing.Any]) -> list[str]:
    nodes = connection.get("nodes")
    if not isinstance(nodes, list):
      raise GitHubGraphQLError("GitHub GraphQL returned invalid List items")
    result: list[str] = []
    for node in nodes:
      node_id = _object(node, "List Repository").get("id")
      if not isinstance(node_id, str):
        raise GitHubGraphQLError("GitHub List Repository omitted its node ID")
      result.append(node_id)
    return result


__all__ = ["GitHubGraphQLAdapter", "GitHubGraphQLError"]
