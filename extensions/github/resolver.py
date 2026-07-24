"""GitHub resolver for handling GitHub blocks."""

from typing import Optional as Opt

from sqlmodel import Session
import sqlmodel
from app.business.info_base.resolver import Resolver
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel
from app.schemas.info_base.main import InArcForm, SubGraphForm
from utils.sql import find_by_json_contains
from .schema import GithubRepo, GithubUser


class GithubRepoResolver(Resolver[GithubRepo, str], rso_type="github_repo"):
  """Resolver for GitHub repository blocks."""

  def __post_init__(self, raw_content: str | None = None) -> None:
    if raw_content is None:
      raise ValueError("GitHub repository blocks require inline JSON content")
    self._content = GithubRepo.model_validate_json(raw_content)
    self.set_solved_content(self._content)

  @classmethod
  def create_graph(
    cls,
    repo: GithubRepo,
    owner: Opt[GithubUser] = None,
  ) -> SubGraphForm:
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
          relation=RelationModel(content="owns"),
          from_subgraph=GithubUserResolver.create_graph(owner),
        ),
      )

    return SubGraphForm(
      in_arcs=in_relations,
      block=BlockModel(
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

  async def get_text(self) -> str:
    """Get text representation of the repository.

    Returns the full name and description.
    """
    text = self._content.full_name
    if self._content.description:
      text += f": {self._content.description}"
    return text

  async def get_str_for_embedding(self) -> str:
    """Get text for embedding generation.

    Combines name, description, topics and language for better semantic search.
    """
    parts = [self._content.full_name]
    if self._content.description:
      parts.append(self._content.description)
    if self._content.language:
      parts.append(f"Language: {self._content.language}")
    if self._content.topics:
      parts.append(f"Topics: {', '.join(self._content.topics)}")
    return "\n".join(parts)


class GithubUserResolver(Resolver[GithubUser, str], rso_type="github_user"):
  """Resolver for GitHub user blocks."""

  def __post_init__(self, raw_content: str | None = None) -> None:
    if raw_content is None:
      raise ValueError("GitHub user blocks require inline JSON content")
    self._content = GithubUser.model_validate_json(raw_content)
    self.set_solved_content(self._content)

  @classmethod
  def create_block(cls, content: GithubUser | dict, storage=None) -> BlockModel:
    return BlockModel(
      resolver=cls.__rsotype__,
      content=GithubUser.model_validate(content).model_dump_json(),
      storage=storage,
    )

  @classmethod
  def create_graph(cls, user: GithubUser | dict) -> SubGraphForm:
    return SubGraphForm(block=cls.create_block(user))

  async def get_text(self) -> str:
    """Get text representation of the GitHub user.

    Returns the display name and login, or just login if no name.
    """
    if self._content.name:
      return f"{self._content.name} (@{self._content.login})"
    return f"@{self._content.login}"

  async def get_str_for_embedding(self) -> str:
    """Use the display representation for semantic retrieval."""
    return await self.get_text()

  def get_existing(self, db_session: Session) -> BlockModel | None:
    """Check for existing GitHub user by ID."""
    existing_block = db_session.exec(
      sqlmodel.select(BlockModel).where(
        BlockModel.resolver == self._block.resolver,
        find_by_json_contains(BlockModel.content, {"id": self._content.id}),
      )
    ).one_or_none()
    return existing_block
