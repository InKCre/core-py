"""Email resolver for handling email blocks."""

from typing import Optional as Opt

from sqlmodel import Session
import sqlmodel
from app.business.info_base.resolver import Resolver
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel
from app.schemas.info_base.main import InArcForm, OutArcForm, SubGraphForm
from utils.sql import find_by_json_contains
from .schema import Email, EmailAddress, Newsletter


class EmailResolver(Resolver, rso_type="email"):
  """Resolver for email blocks."""

  def __post_init__(self):
    """Parse email content after initialization."""
    self.content = Email.model_validate_json(self._block.content)

  @classmethod
  def create_graph(
    cls,
    email: Email,
    from_: EmailAddress,
    to: list[EmailAddress],
    cc: Opt[list[EmailAddress]] = None,
  ) -> SubGraphForm:
    """Create a StarGraphForm from email data.

    :param email: the email
    :param from_: sender email address
    :param to: list of recipient email addresses
    :param cc: optional list of CC recipient email addresses
    :return: StarGraphForm representing the email graph
    ```mermaid
    graph TD
        A[Email Address] -->|from| B[Email]
        B -->|to| C[Email Address]
        B -->|cc| D[Email Address]
    ```
    """
    return SubGraphForm(
      in_arcs=(
        InArcForm(
          relation=RelationModel(content="from"),
          from_subgraph=EmailAddressResolver.create_graph(from_),
        ),
      ),
      block=BlockModel(
        resolver=cls.__rsotype__,
        content=email.model_dump_json(),
      ),
      out_arcs=(
        *(
          OutArcForm(
            relation=RelationModel(content="to"),
            to_subgraph=EmailAddressResolver.create_graph(addr),
          )
          for addr in to
        ),
        *(
          OutArcForm(
            relation=RelationModel(content="cc"),
            to_subgraph=EmailAddressResolver.create_graph(addr),
          )
          for addr in (cc or [])
        ),
      ),
    )

  def get_existing(self, db_session: Session) -> BlockModel | None:
    """Email does not check uniqueness."""
    return None


# TODO
class NewsletterResolver(Resolver, rso_type="newsletter"):
  """Resolver for newsletter blocks."""

  def __post_init__(self):
    """Parse newsletter content after initialization."""
    self.content = Newsletter.model_validate_json(self._block.content)

  @classmethod
  def create_graph(cls, newsletter: Newsletter) -> SubGraphForm:
    """Create a StarGraphForm from newsletter data.

    :param newsletter: Newsletter object to convert to block
    :return: StarGraphForm for the newsletter
    """
    return SubGraphForm(
      block=BlockModel(
        resolver=cls.__rsotype__,
        content=newsletter.model_dump_json(),
      ),
      out_arcs=(),
    )

  async def get_text(self) -> str:
    """Get text representation of the newsletter.

    Returns the newsletter body.
    """
    return self.content.body

  def get_str_for_embedding(self) -> str:
    """Get text for embedding generation.

    Combines subject and body for better semantic search.
    """
    return f"Subject: {self.content.subject}\n\n{self.content.body}"


class EmailAddressResolver(Resolver, rso_type="email_address"):
  """Resolver for email address blocks."""

  def __post_init__(self):
    self._solved_content: EmailAddress = EmailAddress.model_validate_json(
      self._block.content
    )

  @classmethod
  def create_block(cls, content: EmailAddress | dict, storage=None) -> BlockModel:
    return BlockModel(
      resolver=cls.__rsotype__,
      content=EmailAddress.model_validate(content).model_dump_json(),
      storage=storage,
    )

  @classmethod
  def create_graph(cls, email: EmailAddress | dict) -> SubGraphForm:
    return SubGraphForm(block=cls.create_block(email))

  async def get_text(self) -> str:
    """Get text representation of the email address.

    Returns the display name and email, or just email if no name.
    """
    if self._solved_content.name:
      return f"{self._solved_content.name} <{self._solved_content.email}>"
    return self._solved_content.email

  def get_existing(self, db_session: Session) -> BlockModel | None:
    existing_block = db_session.exec(
      sqlmodel.select(BlockModel).where(
        BlockModel.resolver == self._block.resolver,
        find_by_json_contains(BlockModel.content, {"email": self._solved_content.email}),
      )
    ).one_or_none()
    return existing_block
