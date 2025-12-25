"""GitHub extension for InKCre - provides GitHub Stars source."""

import sqlmodel
from fastapi import APIRouter
from app.business.extension.main import ExtensionBase


class GithubExtensionConfig(sqlmodel.SQLModel):
  """Configuration for GitHub extension."""

  ...


class Extension(
  ExtensionBase[GithubExtensionConfig],
  ext_id="github",
  config_cls=GithubExtensionConfig,
):
  """GitHub extension - provides GitHub Stars source for collecting starred repositories."""

  @classmethod
  def _init_resolvers(cls):
    """Initialize GitHub resolvers."""
    from .resolver import GithubRepoResolver  # noqa: F401
    from .resolver import GithubUserResolver  # noqa: F401

  @classmethod
  def _init_sources(cls):
    """Initialize GitHub Stars source."""
    from .stars import Source as GithubStarsSource  # noqa: F401

  @classmethod
  def _register_apis(cls, router: APIRouter):
    """Register API endpoints for GitHub extension."""
    from app.business.source import SourceManager

    router.post("/stars")(
      lambda nickname: SourceManager.create(
        f"extensions.{cls.__extid__}.stars.Source", nickname
      )
    )
