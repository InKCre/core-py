"""Canonical GitHub Block producers and use-time projections."""

from __future__ import annotations

import typing

import sqlmodel

from app.business.info_base.resolver import Resolver, TextProjectionContext
from app.business.info_base.resolver.label import format_label
from app.schemas.info_base.block import BlockForm, BlockModel
from app.schemas.info_base.main import InArcForm, OutArcForm, StarsGraphForm
from app.schemas.info_base.relation import RelationForm
from utils.sql import find_by_json_field

from .schema import GitHubAccount, GitHubList, GitHubRepository


ACCOUNT_RESOLVER_ID = "extensions.github.account.v1"
REPOSITORY_RESOLVER_ID = "extensions.github.repository.v1"
LIST_RESOLVER_ID = "extensions.github.list.v1"


class GitHubGraphIntegrityError(RuntimeError):
  """Exact GitHub graph identity is ambiguous or malformed."""


class _GitHubResolverMixin:
  content_model: typing.ClassVar[type[GitHubAccount | GitHubRepository | GitHubList]]

  def __post_init__(self, raw_content: str | None = None) -> None:
    if raw_content is not None:
      resolver = typing.cast(Resolver[typing.Any, str], self)
      resolver.set_solved_content(self.content_model.model_validate_json(raw_content))

  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> typing.Any:
    del materialize_missing
    resolver = typing.cast(Resolver[typing.Any, str], self)
    return self.content_model.model_validate_json(
      await resolver.get_raw_content(refresh=refresh)
    )

  @classmethod
  def create_block(cls, content, storage=None) -> BlockForm:
    canonical = cls.content_model.model_validate(content)
    return BlockForm(
      resolver=typing.cast(typing.Any, cls).__rsotype__,
      content=canonical.model_dump_json(),
      storage=storage,
    )

  @classmethod
  def create_graph(cls, content) -> StarsGraphForm:
    return StarsGraphForm(block=cls.create_block(content))

  @classmethod
  def find_existing(
    cls,
    node_id: str,
    db_session: sqlmodel.Session,
  ) -> BlockModel | None:
    matches = db_session.exec(
      sqlmodel.select(BlockModel).where(
        BlockModel.resolver == typing.cast(typing.Any, cls).__rsotype__,
        find_by_json_field(BlockModel.content, "node_id", node_id),
      )
    ).all()
    if len(matches) > 1:
      raise GitHubGraphIntegrityError(
        f"GitHub node {node_id!r} resolves to multiple Blocks"
      )
    return matches[0] if matches else None

  def get_existing(self, db_session: sqlmodel.Session) -> BlockModel | None:
    resolver = typing.cast(Resolver[typing.Any, str], self)
    content = self.content_model.model_validate_json(resolver._block.content)
    return self.find_existing(content.node_id, db_session)


class GitHubAccountResolver(
  _GitHubResolverMixin,
  Resolver[GitHubAccount, str],
  rso_type=ACCOUNT_RESOLVER_ID,
):
  """Resolve one GitHub user or organization account."""

  content_model = GitHubAccount

  async def get_text(
    self,
    *,
    context: TextProjectionContext = "default",
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    del context
    account = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    return f"{account.name} (@{account.login})" if account.name else f"@{account.login}"

  async def get_label(self, *, refresh: bool = False) -> str:
    account = GitHubAccount.model_validate_json(await self.get_raw_content(refresh=refresh))
    return format_label(f"github {account.kind}", account.login)


class GitHubRepositoryResolver(
  _GitHubResolverMixin,
  Resolver[GitHubRepository, str],
  rso_type=REPOSITORY_RESOLVER_ID,
):
  """Resolve one GitHub Repository."""

  content_model = GitHubRepository

  @classmethod
  def create_graph(
    cls,
    content: GitHubRepository,
    owner: GitHubAccount | None = None,
  ) -> StarsGraphForm:
    incoming = (
      (
        InArcForm(
          relation=RelationForm(content="owns"),
          from_graph=GitHubAccountResolver.create_graph(owner),
        ),
      )
      if owner is not None
      else ()
    )
    return StarsGraphForm(block=cls.create_block(content), in_arcs=incoming)

  async def get_text(
    self,
    *,
    context: TextProjectionContext = "default",
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    del context
    repository = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    parts = [repository.name_with_owner]
    if repository.description:
      parts.append(repository.description)
    if repository.primary_language:
      parts.append(f"Language: {repository.primary_language}")
    if repository.topics:
      parts.append(f"Topics: {', '.join(repository.topics)}")
    return "\n".join(parts)

  async def get_label(self, *, refresh: bool = False) -> str:
    repository = GitHubRepository.model_validate_json(
      await self.get_raw_content(refresh=refresh)
    )
    return format_label("github repository", repository.name_with_owner)


class GitHubListResolver(
  _GitHubResolverMixin,
  Resolver[GitHubList, str],
  rso_type=LIST_RESOLVER_ID,
):
  """Resolve one GitHub List independently of current membership."""

  content_model = GitHubList

  @classmethod
  def create_graph(
    cls,
    content: GitHubList,
    *,
    owner: GitHubAccount | None = None,
    repositories: typing.Iterable[GitHubRepository] = (),
  ) -> StarsGraphForm:
    incoming = (
      (
        InArcForm(
          relation=RelationForm(content="owns"),
          from_graph=GitHubAccountResolver.create_graph(owner),
        ),
      )
      if owner is not None
      else ()
    )
    outgoing = tuple(
      OutArcForm(
        relation=RelationForm(content="contains"),
        to_graph=GitHubRepositoryResolver.create_graph(repository),
      )
      for repository in repositories
    )
    return StarsGraphForm(
      block=cls.create_block(content),
      in_arcs=incoming,
      out_arcs=outgoing,
    )

  async def get_text(
    self,
    *,
    context: TextProjectionContext = "default",
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    del context
    list_ = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    return "\n".join(part for part in (list_.name, list_.description) if part)

  async def get_label(self, *, refresh: bool = False) -> str:
    list_ = GitHubList.model_validate_json(await self.get_raw_content(refresh=refresh))
    return format_label("github list", list_.name)


__all__ = [
  "ACCOUNT_RESOLVER_ID",
  "GitHubAccountResolver",
  "GitHubGraphIntegrityError",
  "GitHubListResolver",
  "GitHubRepositoryResolver",
  "LIST_RESOLVER_ID",
  "REPOSITORY_RESOLVER_ID",
]
