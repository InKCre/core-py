"""GitHub resolver for handling GitHub blocks."""

from sqlmodel import Session
import sqlmodel
from app.business.info_base.resolver import Resolver
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel
from app.schemas.info_base.main import ArcForm, StarGraphForm
from utils.sql import find_by_json_contains
from .schema import GithubRepo, GithubUser


class GithubRepoResolver(Resolver, rso_type="github_repo"):
  """Resolver for GitHub repository blocks."""

  def __post_init__(self):
    """Parse GitHub repo content after initialization."""
    self.content = GithubRepo.model_validate_json(self._block.content)

  @classmethod
  def create_graph(
    cls,
    repo: GithubRepo,
    owner: GithubUser,
  ) -> StarGraphForm:
    """Create a StarGraphForm from GitHub repository data.

    :param repo: GitHub repository
    :param owner: Repository owner (GitHub user)
    :return: StarGraphForm representing the repository graph
    ```mermaid
    graph TD
        A[GitHub User] -->|owns| B[GitHub Repo]
    ```
    """
    return StarGraphForm(
      in_relations=(
        ArcForm(
          relation=RelationModel(content="owns"),
          from_block=GithubUserResolver.create_graph(owner),
        ),
      ),
      block=BlockModel(
        resolver=cls.__rsotype__,
        content=repo.model_dump_json(),
      ),
      out_relations=(),
    )

  def get_existing(self, db_session: Session) -> BlockModel | None:
    """Check for existing GitHub repo by ID."""
    existing_block = db_session.exec(
      sqlmodel.select(BlockModel).where(
        BlockModel.resolver == self._block.resolver,
        find_by_json_contains(BlockModel.content, {"id": self.content.id}),
      )
    ).one_or_none()
    return existing_block

  async def get_text(self) -> str:
    """Get text representation of the repository.

    Returns the full name and description.
    """
    text = self.content.full_name
    if self.content.description:
      text += f": {self.content.description}"
    return text

  def get_str_for_embedding(self) -> str:
    """Get text for embedding generation.

    Combines name, description, topics and language for better semantic search.
    """
    parts = [self.content.full_name]
    if self.content.description:
      parts.append(self.content.description)
    if self.content.language:
      parts.append(f"Language: {self.content.language}")
    if self.content.topics:
      parts.append(f"Topics: {', '.join(self.content.topics)}")
    return "\n".join(parts)


class GithubUserResolver(Resolver, rso_type="github_user"):
  """Resolver for GitHub user blocks."""

  def __post_init__(self):
    self._solved_content: GithubUser = GithubUser.model_validate_json(
      self._block.content
    )

  @classmethod
  def create_block(cls, content: GithubUser | dict, storage=None) -> BlockModel:
    return BlockModel(
      resolver=cls.__rsotype__,
      content=GithubUser.model_validate(content).model_dump_json(),
      storage=storage,
    )

  @classmethod
  def create_graph(cls, user: GithubUser | dict) -> StarGraphForm:
    return StarGraphForm(block=cls.create_block(user))

  async def get_text(self) -> str:
    """Get text representation of the GitHub user.

    Returns the display name and login, or just login if no name.
    """
    if self._solved_content.name:
      return f"{self._solved_content.name} (@{self._solved_content.login})"
    return f"@{self._solved_content.login}"

  def get_existing(self, db_session: Session) -> BlockModel | None:
    """Check for existing GitHub user by ID."""
    existing_block = db_session.exec(
      sqlmodel.select(BlockModel).where(
        BlockModel.resolver == self._block.resolver,
        find_by_json_contains(BlockModel.content, {"id": self._solved_content.id}),
      )
    ).one_or_none()
    return existing_block
