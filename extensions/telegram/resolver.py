"""Telegram message resolver for handling Telegram message blocks."""

from app.business.info_base.resolver import Resolver
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.main import SubGraphForm
from .schema import TelegramMessage


class TelegramMessageResolver(
  Resolver, rso_type="extensions.telegram.resolver.TelegramMessageResolver"
):
  """Resolver for Telegram message blocks."""

  def __post_init__(self):
    """Parse Telegram message content after initialization."""
    self._resolved_content = TelegramMessage.model_validate_json(self._block.content)

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
    if self._resolved_content.text:
      return self._resolved_content.text
    if self._resolved_content.caption:
      return self._resolved_content.caption

    # Fallback to media type information
    if self._resolved_content.has_media:
      return f"[{self._resolved_content.media_type or 'media'}]"
    return "[empty message]"

  def get_str_for_embedding(self) -> str:
    """Get text for embedding generation.

    Combines message content for semantic search.
    """
    parts = []

    # Add message content
    if self.content.text:
      parts.append(self.content.text)
    elif self.content.caption:
      parts.append(self.content.caption)

    # Add media information
    if self.content.has_media and self.content.media_type:
      parts.append(f"[{self.content.media_type}]")

    return "\n".join(parts) if parts else "[empty message]"
