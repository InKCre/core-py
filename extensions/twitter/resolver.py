import json
from typing import Optional as Opt

from app.business.info_base.resolver import Resolver, TextProjectionContext
from app.business.info_base.resolver.label import format_label
from app.business.info_base.block import BlockManager
from app.schemas.info_base.block import BlockForm
from app.schemas.info_base.main import StarsGraphForm
from .schema import Tweet


class TweetResolver(Resolver[Tweet, str], rso_type="extensions.twitter.tweet.v1"):
  """Tweet Resolver."""

  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> Tweet:
    """Get the solved content (non-cache).

    - attachments will be resolved from `attachment:` out relations
    """
    # Get the base tweet without attachments
    tweet_dict = json.loads(await self.get_raw_content(refresh=refresh))
    tweet = Tweet(**tweet_dict)

    # Fetch attachments
    relations = await self.get_relations(include_in=False, refresh=refresh)
    tweet.attachments = []
    tweet.links = []
    for relation in relations:
      if relation.content.startswith("attachment:") or relation.content == "entities:url":
        attachment_resolver = BlockManager.get_resolver(relation.to_)
        if attachment_resolver:
          solved = await attachment_resolver.get_solved_content(
            refresh=refresh,
            materialize_missing=materialize_missing,
          )
          if relation.content.startswith("attachment:"):
            tweet.attachments.append(solved)
          elif isinstance(solved, str):
            tweet.links.append(solved)

    return tweet

  async def get_text(
    self,
    *,
    context: TextProjectionContext = "default",
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    """Return the text of the tweet."""
    del context
    solved = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    return solved.text

  async def get_label(self, *, refresh: bool = False) -> str:
    root = Tweet.model_validate_json(await self.get_raw_content(refresh=refresh))
    return format_label(
      "tweet",
      root.text or str(root.id),
      first_line=True,
    )

  @classmethod
  def create_block(cls, content: Tweet, storage: Opt[int] = None) -> BlockForm:
    """Create a BlockForm from Tweet."""
    # Remove attachments from the dict for storage
    tweet_dict = content.model_dump()
    tweet_dict.pop("attachments", None)
    tweet_dict.pop("links", None)
    return BlockForm(
      resolver=cls.__rsotype__,
      content=json.dumps(tweet_dict),
      storage=storage,
    )

  @classmethod
  def create_graph(cls, content: Tweet) -> StarsGraphForm:
    """Create a StarsGraphForm from Tweet."""
    block = cls.create_block(content)
    return StarsGraphForm(
      block=block,
      out_arcs=(),
    )
