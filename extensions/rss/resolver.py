"""Feed item resolver for handling RSS/Atom feed item blocks."""

from app.business.info_base.resolver import Resolver
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.main import StarGraphForm

from .schema import FeedItem


class FeedItemResolver(Resolver, rso_type="feed_item"):
  """Resolver for RSS/Atom feed item blocks."""

  def __post_init__(self):
    """Parse feed item content after initialization."""
    self._solved_content = FeedItem.model_validate_json(self._block.content)

  @classmethod
  def create_block(cls, item: FeedItem) -> BlockModel:
    """Create a BlockModel from a FeedItem."""
    return BlockModel(
      resolver=cls.__rsotype__,
      content=item.model_dump_json(),
    )

  @classmethod
  def create_graph(cls, item: FeedItem) -> StarGraphForm:
    """Create a StarGraphForm from a FeedItem."""
    return StarGraphForm(
      block=cls.create_block(item),
      out_relations=(),
    )

  async def get_text(self) -> str:
    """Get text representation of the feed item.

    Returns the content, falling back to summary or title.
    """
    return (
      self._solved_content.content
      or self._solved_content.summary
      or self._solved_content.title
    )

  def get_str_for_embedding(self) -> str:
    """Get text for embedding generation.

    Combines title, summary and content for better semantic search.
    """
    parts = [f"Title: {self._solved_content.title}"]
    if self._solved_content.summary:
      parts.append(f"Summary: {self._solved_content.summary}")
    if self._solved_content.content:
      # Limit content length for embedding
      content_preview = self._solved_content.content[:2000]
      parts.append(f"Content: {content_preview}")
    return "\n\n".join(parts)
