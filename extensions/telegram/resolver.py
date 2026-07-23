"""Telegram message resolver for handling Telegram message blocks."""

from app.business.info_base.resolver import Resolver
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.main import SubGraphForm
from .schema import TelegramMessage


class TelegramMessageResolver(
  Resolver[TelegramMessage, str],
  rso_type="extensions.telegram.resolver.TelegramMessageResolver",
):
  """Resolver for Telegram message blocks."""

  def __post_init__(self, raw_content):
    if raw_content is not None:
      self.set_solved_content(TelegramMessage.model_validate_json(raw_content))

  @classmethod
  def create_graph(cls, message: TelegramMessage) -> SubGraphForm:
    """Create a StarGraphForm from Telegram message data.

    :param message: TelegramMessage object to convert to block
    :return: StarGraphForm for the Telegram message
    """
    return SubGraphForm(
      block=BlockModel(
        resolver=cls.__rsotype__,
        content=message.model_dump_json(),
      ),
      out_arcs=(),
    )

  async def get_text(self) -> str:
    """Get text representation of the Telegram message.

    Returns the message text or caption if available.
    """
    solved_content = await self.get_solved_content()
    if solved_content.text:
      return solved_content.text
    if solved_content.caption:
      return solved_content.caption

    # Fallback to media type information
    if solved_content.has_media:
      return f"[{solved_content.media_type or 'media'}]"
    return "[empty message]"

  async def get_str_for_embedding(self) -> str:
    """Get text for embedding generation.

    Combines message content for semantic search.
    """
    solved_content = await self.get_solved_content()
    parts = []

    # Add message content
    if solved_content.text:
      parts.append(solved_content.text)
    elif solved_content.caption:
      parts.append(solved_content.caption)

    # Add media information
    if solved_content.has_media and solved_content.media_type:
      parts.append(f"[{solved_content.media_type}]")

    return "\n".join(parts) if parts else "[empty message]"
