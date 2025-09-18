import typing
import sqlmodel
from typing import Optional as Opt
from fastapi import APIRouter
from app.business.extension import ExtensionBase
from app.business.source import SourceManager


class TwitterExtensionConfig(sqlmodel.SQLModel):
    client_id: str = ""
    client_secret: str = ""
    backend: typing.Literal["official", "twikit"] = "official"
    email: str = ""
    username: str = ""
    password: str = ""
    totp_secret: Opt[str] = None
    api_language: str = "en-US"
    proxy: Opt[str] = None


class TwitterExtensionState(sqlmodel.SQLModel):
    access_token: Opt[str] = None
    refresh_token: Opt[str] = None
    user_id: str = ""
    user_handle: str = ""
    latest_tweet_id: Opt[int] = None


class Extension(
    ExtensionBase[TwitterExtensionConfig, TwitterExtensionState],
    ext_id="twitter",
    config_cls=TwitterExtensionConfig,
    state_cls=TwitterExtensionState,
):
    @classmethod
    def _init_resolvers(cls):
        from .resolver import TweetResolver

    @classmethod
    def _init_sources(cls):
        from .bookmark import Source as BookmarkSource

    @classmethod
    async def on_close(cls):
        from .api import TwitterAPI

        await TwitterAPI.new().close()

        await super().on_close()

    @classmethod
    def _register_apis(cls, router: APIRouter):
        from .api import TwitterAPI

        TwitterAPI.new(api_router=router)
        router.post("/bookmark")(
            lambda nickname: SourceManager.create(
                f"extensions.{cls.__extid__}.bookmark", nickname
            )
        )
