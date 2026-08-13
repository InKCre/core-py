"""GitHub resolver for handling GitHub blocks."""

from typing import Optional as Opt

from sqlmodel import Session
import sqlmodel
from app.business.info_base.resolver import Resolver, TextProjectionContext
from app.business.info_base.resolver.label import format_label
from app.schemas.info_base.block import BlockForm, BlockModel
from app.schemas.info_base.relation import RelationForm
from app.schemas.info_base.main import InArcForm, StarsGraphForm
from utils.sql import find_by_json_contains
from .schema import GithubRepo, GithubUser


class GithubRepoResolver(
  Resolver[GithubRepo, str],
  rso_type="extensions.github.repo.v1",
):
  """Resolver for GitHub repository blocks."""

  def __post_init__(self, raw_content: str | None = None) -> None:
    if raw_content is None:
      raise ValueError("GitHub repository blocks require inline JSON content")
    self._content = GithubRepo.model_validate_json(raw_content)
    self.set_solved_content(self._content)

  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> GithubRepo:
    del materialize_missing
    self._content = GithubRepo.model_validate_json(
      await self.get_raw_content(refresh=refresh)
    )
    return self._content

  @classmethod
  def create_graph(
    cls,
    repo: GithubRepo,
    owner: Opt[GithubUser] = None,
  ) -> StarsGraphForm:
    """Create a StarGraphForm from GitHub repository data.

    :param repo: GitHub repository
    :param owner: Repository owner (GitHub user), optional
    :return: StarGraphForm representing the repository graph
    ```mermaid
    graph TD
        A[GitHub User] -->|owns| B[GitHub Repo]
    ```
    """
    in_relations = ()
    if owner:
      in_relations = (
        InArcForm(
          relation=RelationForm(content="owns"),
          from_graph=GithubUserResolver.create_graph(owner),
        ),
      )

    return StarsGraphForm(
      in_arcs=in_relations,
      block=BlockForm(
        resolver=cls.__rsotype__,
        content=repo.model_dump_json(),
      ),
      out_arcs=(),
    )

  def get_existing(self, db_session: Session) -> BlockModel | None:
    """Check for existing GitHub repo by ID."""
    existing_block = db_session.exec(
      sqlmodel.select(BlockModel).where(
        BlockModel.resolver == self._block.resolver,
        find_by_json_contains(BlockModel.content, {"id": self._content.id}),
      )
    ).one_or_none()
    return existing_block

  async def get_text(
    self,
    *,
    context: TextProjectionContext = "default",
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    """Return one complete reusable textual projection of the repository."""
    del context
    content = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    parts = [content.full_name]
    if content.description:
      parts.append(content.description)
    if content.language:
      parts.append(f"Language: {content.language}")
    if content.topics:
      parts.append(f"Topics: {', '.join(content.topics)}")
    return "\n".join(parts)

  async def get_label(self, *, refresh: bool = False) -> str:
    content = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=False,
    )
    return format_label("github repository", content.full_name)


class GithubUserResolver(
  Resolver[GithubUser, str],
  rso_type="extensions.github.user.v1",
):
  """Resolver for GitHub user blocks."""

  def __post_init__(self, raw_content: str | None = None) -> None:
    if raw_content is None:
      raise ValueError("GitHub user blocks require inline JSON content")
    self._content = GithubUser.model_validate_json(raw_content)
    self.set_solved_content(self._content)

  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> GithubUser:
    del materialize_missing
    self._content = GithubUser.model_validate_json(
      await self.get_raw_content(refresh=refresh)
    )
    return self._content

  @classmethod
  def create_block(cls, content: GithubUser | dict, storage=None) -> BlockForm:
    return BlockForm(
      resolver=cls.__rsotype__,
      content=GithubUser.model_validate(content).model_dump_json(),
      storage=storage,
    )

  @classmethod
  def create_graph(cls, user: GithubUser | dict) -> StarsGraphForm:
    return StarsGraphForm(block=cls.create_block(user))

  async def get_text(
    self,
    *,
    context: TextProjectionContext = "default",
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    """Get text representation of the GitHub user.

    Returns the display name and login, or just login if no name.
    """
    del context
    content = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    if content.name:
      return f"{content.name} (@{content.login})"
    return f"@{content.login}"

  async def get_label(self, *, refresh: bool = False) -> str:
    content = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=False,
    )
    return format_label("github user", content.login)

  def get_existing(self, db_session: Session) -> BlockModel | None:
    """Check for existing GitHub user by ID."""
    existing_block = db_session.exec(
      sqlmodel.select(BlockModel).where(
        BlockModel.resolver == self._block.resolver,
        find_by_json_contains(BlockModel.content, {"id": self._content.id}),
      )
    ).one_or_none()
    return existing_block
