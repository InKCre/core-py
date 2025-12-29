"""Feed item resolver for handling RSS/Atom feed item blocks."""

from app.business.info_base.resolver import Resolver
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.main import SubGraphForm

from .schema import FeedItem


class FeedItemResolver(Resolver[FeedItem, str], rso_type="feed_item"):
  """Resolver for RSS/Atom feed item blocks."""

  def __post_init__(self, raw_content):
    if raw_content is not None:
      self.set_solved_content(FeedItem.model_validate_json(raw_content))

  @classmethod
  def create_block(cls, content: FeedItem, storage=None) -> BlockModel:
    """Create a BlockModel from a FeedItem."""
    return BlockModel(
      resolver=cls.__rsotype__,
      content=content.model_dump_json(),
      storage=storage,
    )

  @classmethod
  def create_graph(cls, item: FeedItem) -> SubGraphForm:
    """Create a StarGraphForm from a FeedItem."""
    return SubGraphForm(
      block=cls.create_block(item),
      out_arcs=(),
    )

  async def get_text(self) -> str:
    """Get text representation of the feed item.

    Returns the content, falling back to summary or title.
    """
    solved_content = await self.get_solved_content()
    return solved_content.content or solved_content.summary or solved_content.title

  async def get_str_for_embedding(self) -> str:
    """Get text for embedding generation.

    Combines title, summary and content for better semantic search.
    """
    solved_content = await self.get_solved_content()
    parts = [f"Title: {solved_content.title}"]
    if solved_content.summary:
      parts.append(f"Summary: {solved_content.summary}")
    if solved_content.content:
      # Limit content length for embedding
      content_preview = solved_content.content[:2000]
      parts.append(f"Content: {content_preview}")
    return "\n\n".join(parts)
