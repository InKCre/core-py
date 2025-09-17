"""Twitter Bookmark Source"""

import asyncio
import typing
import json
from typing import Optional as Opt
from app.business.block import BlockManager
from app.business.relation import RelationManager
from app.business.resolver import ImageResolver, VideoResolver, WebpageResolver
from app.business.source import SourceBase
from app.schemas.root import StarGraphForm
from app.schemas.block import BlockID, BlockModel
from app.schemas.relation import RelationModel
from app.schemas.root import ArcForm
from extensions.twitter import Extension
from .api import TwitterAPI
from .schema import Tweet, TweetID


class Source(SourceBase):
    """Twitter Bookmark as Source"""

    API_BASE_URL = "https://api.x.com/2"

    async def _collect(  # type: ignore[override]  seems to be a bug of pyright
        self, full: bool = False, page: Opt[str] = None, page_index: int = 0
    ) -> typing.AsyncGenerator[StarGraphForm, None]:
        """Collect all new bookmarks and its notes.

        :param page: Which page to collect.
        :param full: If True, collect until no more pages.

        What is new bookmarks?
        The tweets before the last collected tweet. The last collected tweet
        is the latest created_at tweet block.
        (Potential issue if bookmarks order changes)

        What is bookmark note?
        User can add a note to a bookmark by replying the bookmark tweet.

        Docs https://docs.x.com/x-api/bookmarks/get-bookmarks
        """
        RESULT_LIMIT = 40
        api_client = TwitterAPI.new()
        bookmarks_res = await api_client.get_bookmarks(
            page=page, max_results=RESULT_LIMIT
        )

        # find new tweets start point
        old_start_at = len(bookmarks_res.tweets)
        if not full:
            latest_tweet_id = Extension.state.latest_tweet_id
            if latest_tweet_id:
                old_start_at = next(
                    (
                        i
                        for i, tweet in enumerate(bookmarks_res.tweets)
                        if tweet.id == latest_tweet_id
                    ),
                    len(bookmarks_res.tweets),
                )

        for tweet in (
            bookmarks_res.tweets
            if full
            else reversed(bookmarks_res.tweets[:old_start_at])
        ):
            yield StarGraphForm(
                block=BlockModel(
                    resolver=Tweet.__resolver__.__rsotype__,
                    content=Tweet(**tweet.model_dump()).model_dump_json(),
                ),
                out_relations=tuple(
                    ArcForm(
                        relation=RelationModel(content="attachment:photo"),
                        to_block=ImageResolver.create_brs(
                            url=photo.url, alt_text=photo.alt_text
                        ),
                    )
                    for photo in tweet.photos
                )
                + tuple(
                    ArcForm(
                        relation=RelationModel(content="attachment:video"),
                        to_block=VideoResolver.create_brs(url=video.variants[0].url),
                    )
                    for video in tweet.videos
                )
                + tuple(
                    ArcForm(
                        relation=RelationModel(content="entities:url"),
                        to_block=WebpageResolver.create_brs(url=url),
                    )
                    for url in tweet.urls
                ),
            )

        if (full and page_index == 0) or not full:
            Extension.state.latest_tweet_id = bookmarks_res.tweets[0].id

        if full and bookmarks_res.next_page and bookmarks_res.next_page != page:
            await asyncio.sleep(10)
            async for i in self._collect(
                page=bookmarks_res.next_page, full=full, page_index=page_index + 1
            ):
                yield i

    async def _organize(self, block_id: BlockID) -> None:
        block = BlockManager.get(block_id)
        if not block:
            # TODO log error
            return
        if block.resolver != Tweet.__resolver__.__rsotype__:
            return
        bookmarked_tweet = Tweet.model_validate_json(block.content)
        api_client = TwitterAPI.new()

        # collect notes
        replies = (
            await api_client.get_replies(
                str(bookmarked_tweet.id), from_=api_client.user_handle
            )
        ).tweets
        for reply in replies:
            if not reply.conversation_id:
                # TODO log warning
                continue

            reply_block = BlockManager.create(
                BlockModel(resolver="text", content=reply.text)
            )
            RelationManager.create(
                from_=typing.cast(BlockID, block.id),
                to_=typing.cast(BlockID, reply_block.id),
                content="bookmarked for",
            )

        # resolver = Tweet.__resolver__(bookmarked_tweet)
        # resolver.
