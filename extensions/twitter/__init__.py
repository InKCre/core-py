import typing
import sqlmodel
from typing import Optional as Opt
from fastapi import APIRouter
from app.business.extension.main import ExtensionBase, PublicHTTPRoute
from app.business.info_base.resolver import ResolverManager
from app.business.source import SourceManager

from .setup_flow import TwitterExtensionState


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
  state_cls=TwitterExtensionState,
):
  @classmethod
  def update_config(
    cls,
    new_config: dict[str, typing.Any] | TwitterExtensionConfig,
  ) -> TwitterExtensionConfig:
    from .setup_flow import TwitterExtensionState, _fingerprint, _terminal

    updated = (
      TwitterExtensionConfig.model_validate(new_config)
      if isinstance(new_config, dict)
      else new_config
    )

    def replace(config_model, state_model):
      current_config = TwitterExtensionConfig.model_validate(config_model.model_dump())
      state = TwitterExtensionState.model_validate(state_model.model_dump())
      if _fingerprint(current_config) != _fingerprint(updated):
        state.account = None
        state.oauth_transactions = {
          key: _terminal(value, "expired", error="OAuth App changed")
          if value.status in {"pending", "exchanging"}
          else value
          for key, value in state.oauth_transactions.items()
        }
      return updated, state

    config, _ = cls.mutate_config_and_state(replace)
    return config

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
    from .setup_flow import register_setup_routes

    register_setup_routes(router)

  @classmethod
  def public_http_routes(cls) -> tuple[PublicHTTPRoute, ...]:
    return (PublicHTTPRoute(method="GET", path="/auth/callback"),)
