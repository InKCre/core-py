"""Email resolver for handling email blocks."""

from typing import Optional as Opt

from sqlmodel import Session
import sqlmodel
from app.business.info_base.resolver import Resolver
from app.business.info_base.resolver.label import format_label
from app.schemas.info_base.block import BlockForm, BlockModel
from app.schemas.info_base.relation import RelationForm
from app.schemas.info_base.main import OutArcForm, StarsGraphForm
from utils.sql import find_by_json_contains
from .schema import Email, EmailAddress, Newsletter


class EmailResolver(
  Resolver[Email, str],
  rso_type="extensions.mail.email.v1",
):
  """Resolver for email blocks."""

  def __post_init__(self, raw_content=None):
    """Parse email content after initialization."""
    if raw_content is not None:
      self.set_solved_content(Email.model_validate_json(raw_content))

  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> Email:
    del materialize_missing
    return Email.model_validate_json(await self.get_raw_content(refresh=refresh))

  @classmethod
  def create_graph(
    cls,
    email: Email,
    from_: EmailAddress,
    to: list[EmailAddress],
    cc: Opt[list[EmailAddress]] = None,
  ) -> StarsGraphForm:
    """Create a StarGraphForm from email data.

    :param email: the email
    :param from_: sender email address
    :param to: list of recipient email addresses
    :param cc: optional list of CC recipient email addresses
    :return: StarGraphForm representing the email graph
    ```mermaid
    graph TD
        B[Email] -->|from| A[Email Address]
        B -->|to| C[Email Address]
        B -->|cc| D[Email Address]
    ```
    """
    return StarsGraphForm(
      block=BlockForm(
        resolver=cls.__rsotype__,
        content=email.model_dump_json(),
      ),
      out_arcs=(
        OutArcForm(
          relation=RelationForm(content="from"),
          to_graph=EmailAddressResolver.create_graph(from_),
        ),
        *(
          OutArcForm(
            relation=RelationForm(content="to"),
            to_graph=EmailAddressResolver.create_graph(addr),
          )
          for addr in to
        ),
        *(
          OutArcForm(
            relation=RelationForm(content="cc"),
            to_graph=EmailAddressResolver.create_graph(addr),
          )
          for addr in (cc or [])
        ),
      ),
    )

  def get_existing(self, db_session: Session) -> BlockModel | None:
    """Email does not check uniqueness."""
    return None

  async def get_text(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    email = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    body = email.body_text or email.body_html or ""
    return f"Subject: {email.subject}\n\n{body}"

  async def get_label(self, *, refresh: bool = False) -> str:
    email = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=False,
    )
    return format_label("email", email.subject)


# TODO
class NewsletterResolver(
  Resolver[Newsletter, str],
  rso_type="extensions.mail.newsletter.v1",
):
  """Resolver for newsletter blocks."""

  def __post_init__(self, raw_content=None):
    """Parse newsletter content after initialization."""
    if raw_content is not None:
      self.set_solved_content(Newsletter.model_validate_json(raw_content))

  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> Newsletter:
    del materialize_missing
    return Newsletter.model_validate_json(await self.get_raw_content(refresh=refresh))

  @classmethod
  def create_graph(cls, newsletter: Newsletter) -> StarsGraphForm:
    """Create a StarGraphForm from newsletter data.

    :param newsletter: Newsletter object to convert to block
    :return: StarGraphForm for the newsletter
    """
    return StarsGraphForm(
      block=BlockForm(
        resolver=cls.__rsotype__,
        content=newsletter.model_dump_json(),
      ),
      out_arcs=(),
    )

  async def get_text(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    """Return the newsletter subject and body as one reusable projection."""
    newsletter = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    return f"Subject: {newsletter.subject}\n\n{newsletter.body}"

  async def get_label(self, *, refresh: bool = False) -> str:
    newsletter = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=False,
    )
    return format_label("newsletter", newsletter.subject)


class EmailAddressResolver(
  Resolver[EmailAddress, str],
  rso_type="extensions.mail.email_address.v1",
):
  """Resolver for email address blocks."""

  def __post_init__(self, raw_content=None):
    if raw_content is not None:
      self.set_solved_content(EmailAddress.model_validate_json(raw_content))

  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> EmailAddress:
    del materialize_missing
    return EmailAddress.model_validate_json(await self.get_raw_content(refresh=refresh))

  @classmethod
  def create_block(cls, content: EmailAddress | dict, storage=None) -> BlockForm:
    return BlockForm(
      resolver=cls.__rsotype__,
      content=EmailAddress.model_validate(content).model_dump_json(),
      storage=storage,
    )

  @classmethod
  def create_graph(cls, email: EmailAddress | dict) -> StarsGraphForm:
    return StarsGraphForm(block=cls.create_block(email))

  async def get_text(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    """Get text representation of the email address.

    Returns the display name and email, or just email if no name.
    """
    address = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    if address.name:
      return f"{address.name} <{address.email}>"
    return address.email

  async def get_label(self, *, refresh: bool = False) -> str:
    address = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=False,
    )
    identifier = f"{address.name} / {address.email}" if address.name else address.email
    return format_label("email address", identifier)

  def get_existing(self, db_session: Session) -> BlockModel | None:
    existing_block = db_session.exec(
      sqlmodel.select(BlockModel).where(
        BlockModel.resolver == self._block.resolver,
        find_by_json_contains(
          BlockModel.content,
          {"email": EmailAddress.model_validate_json(self._block.content).email},
        ),
      )
    ).one_or_none()
    return existing_block
