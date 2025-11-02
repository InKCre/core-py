import sqlmodel
from app.business.extension import ExtensionBase
from app.business.source import SourceManager

class GithubExtensionConfig(sqlmodel.SQLModel):
    access_token: str = ""


class GithubExtensionState(sqlmodel.SQLModel):
    pass


class Extension(
    ExtensionBase[GithubExtensionConfig, GithubExtensionState],
    ext_id="github",
    config_cls=GithubExtensionConfig,
    state_cls=GithubExtensionState,
):
    @classmethod
    def _init_resolvers(cls):
        pass

    @classmethod
    def _init_sources(cls):
        from .source import GithubStarSource

    @classmethod
    def _register_apis(cls, router):
        from .source import GithubStarSource
        router.post("/star/{nickname}")(
            lambda nickname: SourceManager.create(
                f"extensions.{cls.__extid__}.{GithubStarSource.source_id}", nickname
            )
        )
