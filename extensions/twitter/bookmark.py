"""Twitter Bookmark Source"""

import pydantic
import sqlmodel
from app.business.info_base.main import InfoBaseManager
from app.business.info_base.resolver import ImageResolver, VideoResolver, HTMLResolver
from app.business.source import SourceBase
from app.engine import SessionLocal
from app.schemas.info_base.main import OutArcForm, StarsGraphForm
from app.schemas.info_base.relation import RelationForm
from app.schemas.job import JobModel
from .api import TwitterAPI
from .resolver import TweetResolver
from .schema import Tweet


class SourceConfig(sqlmodel.SQLModel):
  """Configuration for Twitter Bookmark Source."""

  ...


class CollectConfig(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid")

  full: bool = False
  result_limit: int = pydantic.Field(default=40, ge=5, le=100)


def _video_url(video) -> str | None:
  supported = tuple(
    variant
    for variant in video.variants
    if variant.url and variant.content_type in {None, "video/mp4"}
  )
  selected = max(supported, key=lambda variant: variant.bitrate or -1, default=None)
  return selected.url if selected is not None else None


def tweet_to_graph(tweet) -> StarsGraphForm:
  """Map one Twitter API DTO into the persisted root and relation-owned links."""
  canonical = Tweet(
    id=tweet.id,
    user_id=tweet.user_id,
    conversation_id=tweet.conversation_id,
    quote=tweet.quote,
    text=tweet.text,
  )
  videos = tuple(
    (video, url) for video in tweet.videos if (url := _video_url(video)) is not None
  )
  return StarsGraphForm(
    block=TweetResolver.create_block(canonical),
    out_arcs=tuple(
      OutArcForm(
        relation=RelationForm(content=f"attachment:photo:{photo.id}"),
        to_graph=ImageResolver.create_graph(url=photo.url, alt_text=photo.alt_text),
      )
      for photo in tweet.photos
    )
    + tuple(
      OutArcForm(
        relation=RelationForm(content=f"attachment:video:{video.id}"),
        to_graph=VideoResolver.create_graph(url=url),
      )
      for video, url in videos
    )
    + tuple(
      OutArcForm(
        relation=RelationForm(content="entities:url"),
        to_graph=HTMLResolver.create_graph(url=url),
      )
      for url in tweet.urls
    ),
  )


class Source(
  SourceBase[SourceConfig],
  config_cls=SourceConfig,
  collect_config_cls=CollectConfig,
):
  """Twitter Bookmark as Source"""

  API_BASE_URL = "https://api.x.com/2"

  async def collect(self, job: JobModel, config: pydantic.BaseModel) -> None:
    """Collect all new bookmarks and its notes.

    What is new bookmarks?
    The tweets before the last collected tweet. The last collected tweet
    is the latest created_at tweet block.
    (Potential issue if bookmarks order changes)

    What is bookmark note?
    User can add a note to a bookmark by replying the bookmark tweet.

    Docs https://docs.x.com/x-api/bookmarks/get-bookmarks
    """
    collect_config = CollectConfig.model_validate(config)
    full = collect_config.full
    result_limit = collect_config.result_limit

    page = job.state.get("page") if job.state else None

    api_client = TwitterAPI.new()
    bookmarks_res = await api_client.get_bookmarks(page=page, max_results=result_limit)

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
      collected.append(tweet_to_graph(tweet))

    if not full and bookmarks_res.tweets:
      state = self.get_state()
      state["latest_tweet_id"] = bookmarks_res.tweets[0].id
      self.set_state(state)

    with SessionLocal() as db:
      for graph in reversed(collected) if full else collected:
        await InfoBaseManager.add_stars_graph_to_session(graph, db)
      db.commit()

    # Update job state for next page if full and has next_page
    if full and bookmarks_res.next_page and bookmarks_res.next_page != page:
      job.state = job.state or {}
      job.state["page"] = bookmarks_res.next_page
      with SessionLocal() as db:
        db.add(job)
        db.commit()
