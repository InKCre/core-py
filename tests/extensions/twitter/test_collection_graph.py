"""Twitter API DTO to graph and exact resolver regression."""

import asyncio

from app.business.info_base.resolver import HTMLResolver, ImageResolver, VideoResolver
from app.schemas.info_base.block import BlockModel
from extensions.twitter.api import Tweet as APITweet
from extensions.twitter.bookmark import Source, tweet_to_graph
from extensions.twitter.resolver import TweetResolver
from extensions.twitter.schema import Tweet, TweetPhoto, TweetVideo, VideoVariant


def _api_tweet() -> APITweet:
  return APITweet(
    id=17,
    user_id="author-id",
    conversation_id=9,
    text="A photo [photo], video [video], and link [link]",
    photos=(
      TweetPhoto(
        id="photo-key",
        url="https://media.example/photo.png",
        alt_text="A blue diagram",
      ),
    ),
    videos=(
      TweetVideo(
        id="video-key",
        variants=(
          VideoVariant(
            bitrate=128_000,
            content_type="video/mp4",
            url="https://media.example/low.mp4",
          ),
          VideoVariant(
            bitrate=512_000,
            content_type="video/mp4",
            url="https://media.example/high.mp4",
          ),
        ),
      ),
    ),
    urls=("https://example.test/article",),
  )


def test_api_tweet_maps_to_versioned_root_and_relation_owned_content():
  graph = tweet_to_graph(_api_tweet())
  canonical = Tweet.model_validate_json(graph.block.content)

  assert graph.block.resolver == "extensions.twitter.tweet.v1"
  assert graph.block.storage is None
  assert "photo.png" not in graph.block.content
  assert "high.mp4" not in graph.block.content
  assert "article" not in graph.block.content
  assert [arc.relation.content for arc in graph.out_arcs] == [
    "attachment:photo:photo-key",
    "attachment:video:video-key",
    "entities:url",
  ]
  photo, video, link = (arc.to_graph.block for arc in graph.out_arcs)
  assert (photo.resolver, photo.storage, photo.content) == (
    ImageResolver.__rsotype__,
    -1,
    "https://media.example/photo.png",
  )
  assert (video.resolver, video.storage, video.content) == (
    VideoResolver.__rsotype__,
    -1,
    "https://media.example/high.mp4",
  )
  assert (link.resolver, link.storage, link.content) == (
    HTMLResolver.__rsotype__,
    -1,
    "https://example.test/article",
  )
  assert canonical.id == 17
  assert canonical.conversation_id == 9
  assert canonical.attachments is None
  assert canonical.links is None


def test_tweet_root_resolver_preserves_reply_scope_and_text():
  graph = tweet_to_graph(_api_tweet())
  resolver = TweetResolver(BlockModel.model_validate(graph.block), ())

  solved = asyncio.run(resolver.get_solved_content())

  assert solved.id == 17
  assert solved.user_id == "author-id"
  assert solved.conversation_id == 9
  assert solved.attachments == []
  assert solved.links == []
  assert asyncio.run(resolver.get_text()) == _api_tweet().text


def test_legacy_organization_hook_does_not_invent_bookmark_note_graph():
  asyncio.run(Source(1)._organize(70))
