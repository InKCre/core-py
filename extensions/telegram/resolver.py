"""Telegram message resolver for handling Telegram message blocks."""

from app.business.resolver import Resolver
from app.schemas.block import BlockModel
from app.schemas.root import StarGraphForm
from .schema import TelegramMessage


class TelegramMessageResolver(Resolver, rso_type="extensions.telegram.resolver.TelegramMessageResolver"):
    """Resolver for Telegram message blocks."""

    def __post_init__(self):
        """Parse Telegram message content after initialization."""
        self.content = TelegramMessage.model_validate_json(self._block.content)

    @classmethod
    def create_brs(cls, message: TelegramMessage) -> StarGraphForm:
        """Create a StarGraphForm from Telegram message data.
        
        :param message: TelegramMessage object to convert to block
        :return: StarGraphForm for the Telegram message
        """
        return StarGraphForm(
            block=BlockModel(
                resolver=cls.__rsotype__,
                content=message.model_dump_json(),
            ),
            out_relations=()
        )

    async def get_text(self) -> str:
        """Get text representation of the Telegram message.
        
        Returns the message text or caption if available.
        """
        if self.content.text:
            return self.content.text
        if self.content.caption:
            return self.content.caption
        
        # Fallback to sender info and media type
        sender = self.content.from_user
        sender_info = f"From: @{sender.username}" if sender and sender.username else "From: Unknown"
        if self.content.has_media:
            return f"{sender_info} (sent {self.content.media_type or 'media'})"
        return f"{sender_info} (empty message)"

    def get_str_for_embedding(self) -> str:
        """Get text for embedding generation.
        
        Combines sender info and message content for better semantic search.
        """
        parts = []
        
        # Add sender information
        if self.content.from_user:
            if self.content.from_user.username:
                parts.append(f"From: @{self.content.from_user.username} ({self.content.from_user.first_name})")
            else:
                parts.append(f"From: {self.content.from_user.first_name}")
        
        # Add chat information
        if self.content.chat.title:
            parts.append(f"Chat: {self.content.chat.title}")
        
        # Add message content
        if self.content.text:
            parts.append(f"\n{self.content.text}")
        elif self.content.caption:
            parts.append(f"\n{self.content.caption}")
        
        # Add media information
        if self.content.has_media and self.content.media_type:
            parts.append(f"[{self.content.media_type}]")
        
        return "\n".join(parts)


# Register resolver with TelegramMessage schema
TelegramMessage.__resolver__ = TelegramMessageResolver
