"""Twitter Bookmark Source"""

import typing

import sqlmodel
from app.business.info_base.block import BlockManager
from app.business.info_base.main import InfoBaseManager
from app.business.info_base.relation import RelationManager
from app.business.info_base.resolver import ImageResolver, VideoResolver, HTMLResolver
from app.business.source import SourceBase
from app.engine import SessionLocal
from app.schemas.info_base.main import OutArcForm, SubGraphForm
from app.schemas.info_base.block import BlockID, BlockModel
from app.schemas.info_base.relation import RelationModel
from app.schemas.source import SourceCollectJobModel
from .api import TwitterAPI
from .resolver import TweetResolver
from .schema import Tweet


class SourceConfig(sqlmodel.SQLModel):
  """Configuration for Twitter Bookmark Source."""

  ...


class Source(SourceBase[SourceConfig], config_cls=SourceConfig):
  """Twitter Bookmark as Source"""

  API_BASE_URL = "https://api.x.com/2"

  def scheduled_collect_config(self) -> dict[str, typing.Any]:
    from .setup_flow import TwitterExtensionState, TwitterSetupConflict
    from . import Extension

    state = TwitterExtensionState.model_validate(Extension.get_state().model_dump())
    if state.account is None or state.account.reconnect_required:
      raise TwitterSetupConflict("Twitter account is not connected")
    return {
      "full": False,
      "result_limit": 40,
      "authorization_id": state.account.authorization_id,
    }

  async def collect(self, job: "SourceCollectJobModel") -> None:
    """Collect all new bookmarks and its notes.

    What is new bookmarks?
    The tweets before the last collected tweet. The last collected tweet
    is the latest created_at tweet block.
    (Potential issue if bookmarks order changes)

    What is bookmark note?
    User can add a note to a bookmark by replying the bookmark tweet.

    Docs https://docs.x.com/x-api/bookmarks/get-bookmarks
    """
    config = job.config or {}
    full = config.get("full", False)
    result_limit = config.get("result_limit", 40)
    authorization_id = config.get("authorization_id")
    if not isinstance(authorization_id, str) or not authorization_id:
      raise RuntimeError("Twitter collect job has no authorization identity")

    page = job.state.get("page") if job.state else None

    api_client = TwitterAPI.new(expected_authorization_id=authorization_id)
    try:
      bookmarks_res = await api_client.get_bookmarks(page=page, max_results=result_limit)
    finally:
      await api_client.close()

    # find new tweets start point
    old_start_at = len(bookmarks_res.tweets)
    if not full:
      state = self.get_state()
      latest_tweet_id = state.get("latest_tweet_id")
      if latest_tweet_id:
        old_start_at = next(
          (
            i for i, tweet in enumerate(bookmarks_res.tweets) if tweet.id == latest_tweet_id
          ),
          len(bookmarks_res.tweets),
        )

    collected = []
    for tweet in (
      bookmarks_res.tweets if full else reversed(bookmarks_res.tweets[:old_start_at])
    ):
      collected.append(
        SubGraphForm(
          block=BlockModel(
            resolver=TweetResolver.__rsotype__,
            content=Tweet(**tweet.model_dump()).model_dump_json(),
          ),
          out_arcs=tuple(
            OutArcForm(
              relation=RelationModel(content="attachment:photo"),
              to_subgraph=ImageResolver.create_graph(
                url=photo.url, alt_text=photo.alt_text
              ),
            )
            for photo in tweet.photos
          )
          + tuple(
            OutArcForm(
              relation=RelationModel(content="attachment:video"),
              to_subgraph=VideoResolver.create_graph(url=video.variants[0].url),
            )
            for video in tweet.videos
          )
          + tuple(
            OutArcForm(
              relation=RelationModel(content="entities:url"),
              to_subgraph=HTMLResolver.create_graph(url=url),
            )
            for url in tweet.urls
          ),
        )
      )

    if not full and bookmarks_res.tweets:
      state = self.get_state()
      state["latest_tweet_id"] = bookmarks_res.tweets[0].id
      self.set_state(state)

    with SessionLocal() as db:
      for graph in reversed(collected) if full else collected:
        await InfoBaseManager.add_subgraph_to_session(graph, db)
      db.commit()

    # Update job state for next page if full and has next_page
    if full and bookmarks_res.next_page and bookmarks_res.next_page != page:
      job.state = job.state or {}
      job.state["page"] = bookmarks_res.next_page
      with SessionLocal() as db:
        db.add(job)
        db.commit()

  async def _organize(self, block_id: BlockID) -> None:
    block = BlockManager.get(block_id)
    if not block:
      # TODO log error
      return
    if block.resolver != TweetResolver.__rsotype__:
      return
    bookmarked_tweet = Tweet.model_validate_json(block.content)
    api_client = TwitterAPI.new()

    # collect notes
    replies = (
      await api_client.get_replies(str(bookmarked_tweet.id), from_=api_client.user_handle)
    ).tweets
    for reply in replies:
      if not reply.conversation_id:
        # TODO log warning
        continue

      reply_block = BlockManager.create(BlockModel(resolver="text", content=reply.text))
      RelationManager.create(
        from_=typing.cast(BlockID, block.id),
        to_=typing.cast(BlockID, reply_block.id),
        content="bookmarked for",
      )

    # resolver = Tweet.__resolver__(bookmarked_tweet)
    # resolver.
