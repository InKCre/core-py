"""Telegram message resolver for handling Telegram message blocks."""

from app.business.info_base.resolver import Resolver, TextProjectionContext
from app.business.info_base.resolver.label import format_label
from app.schemas.info_base.block import BlockForm
from app.schemas.info_base.main import StarsGraphForm
from .schema import TelegramMessage


class TelegramMessageResolver(
  Resolver[TelegramMessage, str],
  rso_type="extensions.telegram.message.v1",
):
  """Resolver for Telegram message blocks."""

  def __post_init__(self, raw_content):
    if raw_content is not None:
      self.set_solved_content(TelegramMessage.model_validate_json(raw_content))

  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> TelegramMessage:
    del materialize_missing
    return TelegramMessage.model_validate_json(await self.get_raw_content(refresh=refresh))

  @classmethod
  def create_graph(cls, message: TelegramMessage) -> StarsGraphForm:
    """Create a StarGraphForm from Telegram message data.

    :param message: TelegramMessage object to convert to block
    :return: StarGraphForm for the Telegram message
    """
    return StarsGraphForm(
      block=BlockForm(
        resolver=cls.__rsotype__,
        content=message.model_dump_json(),
      ),
      out_arcs=(),
    )

  async def get_text(
    self,
    *,
    context: TextProjectionContext = "default",
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str | None:
    """Get text representation of the Telegram message.

    Returns the message text or caption if available.
    """
    del context
    solved_content = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    parts = []

    # Add message content
    if solved_content.text:
      parts.append(solved_content.text)
    elif solved_content.caption:
      parts.append(solved_content.caption)

    # Add media information
    if solved_content.has_media and solved_content.media_type:
      parts.append(f"[{solved_content.media_type}]")

    return "\n".join(parts) or None

  async def get_label(self, *, refresh: bool = False) -> str:
    message = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=False,
    )
    identifier = message.text or message.caption or str(message.message_id)
    return format_label("telegram message", identifier, first_line=True)
