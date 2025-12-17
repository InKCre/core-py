import typing
import sqlmodel
from typing import Optional as Opt
from fastapi import APIRouter
from app.business.extension import ExtensionBase
from app.business.source import SourceManager


class TwitterExtensionConfig(sqlmodel.SQLModel):
    # TODO move to SourceConfig
    backend: typing.Literal["official", "twikit"] = "official"
    api_language: str = "en-US"
    proxy: Opt[str] = None
    client_id: str = ""
    client_secret: str = ""
    email: str = ""
    username: str = ""
    password: str = ""
    totp_secret: Opt[str] = None


class Extension(
    ExtensionBase[TwitterExtensionConfig],
    ext_id="twitter",
    config_cls=TwitterExtensionConfig,
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
