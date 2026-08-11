import typing
import sqlmodel
from typing import Optional as Opt
from fastapi import APIRouter
from app.business.extension.main import ExtensionBase
from app.business.info_base.resolver import ResolverManager
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

    ResolverManager.register_resolver(TweetResolver)

  @classmethod
  def _init_sources(cls):
    from .bookmark import Source as BookmarkSource

    SourceManager.add_source_type(BookmarkSource)

  @classmethod
  async def on_close(cls):
    from .api import TwitterAPI

    failures: list[Exception] = []
    try:
      await TwitterAPI.close_singleton()
    except Exception as error:
      failures.append(error)
    try:
      await super().on_close()
    except Exception as error:
      failures.append(error)
    if len(failures) == 1:
      raise failures[0]
    if failures:
      raise ExceptionGroup("Twitter Extension close failed", failures)

  @classmethod
  def _register_apis(cls, router: APIRouter):
    from .api import TwitterAPI

    TwitterAPI.new(api_router=router)
    router.post("/bookmark")(
      lambda nickname: SourceManager.create(
        f"extensions.{cls.__extid__}.bookmark.Source", nickname
      )
    )
