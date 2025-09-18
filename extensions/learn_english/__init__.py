import sqlmodel
from app.business.extension import ExtensionBase


class LearnEnglishConfig(sqlmodel.SQLModel): ...


class LearnEnglishState(sqlmodel.SQLModel): ...


class Extension(
    ExtensionBase[LearnEnglishConfig, LearnEnglishState],
    ext_id="learn_english",
    config_cls=LearnEnglishConfig,
    state_cls=LearnEnglishState,
):
    @classmethod
    def _init_resolvers(cls):
        from .resolver import LexicalResolver
