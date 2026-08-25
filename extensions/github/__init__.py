"""GitHub Stars and Lists collection Extension."""

import sqlmodel
from app.business.extension.main import ExtensionBase


class GithubExtensionConfig(sqlmodel.SQLModel):
  """Configuration for GitHub extension."""

  ...


class Extension(
  ExtensionBase[GithubExtensionConfig],
  ext_id="github",
  config_cls=GithubExtensionConfig,
):
  """Synchronize GitHub Stars and Lists into reusable graph facts."""

  @classmethod
  def _init_resolvers(cls):
    from .resolver import GitHubAccountResolver  # noqa: F401
    from .resolver import GitHubListResolver  # noqa: F401
    from .resolver import GitHubRepositoryResolver  # noqa: F401

  @classmethod
  def _init_sources(cls):
    from .stars import Source as GitHubStarsSource  # noqa: F401
