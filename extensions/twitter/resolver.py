import json
from typing import Optional as Opt

from app.business.info_base.resolver import Resolver
from app.business.info_base.block import BlockManager
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.main import SubGraphForm
from .schema import Tweet


class TweetResolver(Resolver[Tweet, str], rso_type="extensions.twitter.tweet"):
  """Tweet Resolver."""

  async def _get_solved_content(self) -> Tweet:
    """Get the solved content (non-cache).

    - attachments will be resolved from `attachment:` out relations
    """
    # Get the base tweet without attachments
    tweet_dict = json.loads(await self.get_raw_content())
    tweet = Tweet(**tweet_dict)

    # Fetch attachments
    relations = await self.get_relations(include_in=False)
    tweet.attachments = []
    for relation in relations:
      if relation.content.startswith("attachment:"):
        attachment_resolver = BlockManager.get_resolver(relation.to_)
        if attachment_resolver:
          tweet.attachments.append(await attachment_resolver.get_solved_content())

    return tweet

  async def get_text(self) -> str:
    """Return the text of the tweet."""
    solved = await self.get_solved_content()
    return solved.text

  async def get_str_for_embedding(self) -> str:
    """Return the text for embedding."""
    return await self.get_text()

  @classmethod
  def create_block(cls, content: Tweet, storage: Opt[int] = None) -> BlockModel:
    """Create a BlockModel from Tweet."""
    # Remove attachments from the dict for storage
    tweet_dict = content.model_dump()
    tweet_dict.pop("attachments", None)
    return BlockModel(
      resolver=cls.__rsotype__,
      content=json.dumps(tweet_dict),
      storage=storage,
    )

  @classmethod
  def create_graph(cls, content: Tweet) -> SubGraphForm:
    """Create a SubGraphForm from Tweet."""
    block = cls.create_block(content)
    return SubGraphForm(
      block=block,
      out_arcs=(),
    )
