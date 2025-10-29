"""Email resolver for handling email blocks."""

from app.business.resolver import Resolver
from app.schemas.block import BlockModel
from app.schemas.root import StarGraphForm
from .schema import Email


class EmailResolver(Resolver, rso_type="extensions.mail.resolver.EmailResolver"):
    """Resolver for email blocks."""

    def __post_init__(self):
        """Parse email content after initialization."""
        self.content = Email.model_validate_json(self._block.content)

    @classmethod
    def create_brs(cls, email: Email) -> StarGraphForm:
        """Create a StarGraphForm from email data.
        
        :param email: Email object to convert to block
        :return: StarGraphForm for the email
        """
        return StarGraphForm(
            block=BlockModel(
                resolver=cls.__rsotype__,
                content=email.model_dump_json(),
            ),
            out_relations=()
        )

    async def get_text(self) -> str:
        """Get text representation of the email.
        
        Returns the plain text body if available, otherwise a summary.
        """
        if self.content.body_text:
            return self.content.body_text
        
        # Fallback to subject and sender info
        return f"Subject: {self.content.subject}\nFrom: {self.content.from_.email}"

    def get_str_for_embedding(self) -> str:
        """Get text for embedding generation.
        
        Combines subject and body for better semantic search.
        """
        parts = [f"Subject: {self.content.subject}"]
        
        if self.content.from_.name:
            parts.append(f"From: {self.content.from_.name} <{self.content.from_.email}>")
        else:
            parts.append(f"From: {self.content.from_.email}")
        
        if self.content.body_text:
            parts.append(f"\n{self.content.body_text}")
        
        return "\n".join(parts)


# Register resolver with Email schema
Email.__resolver__ = EmailResolver
