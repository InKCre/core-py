import sqlmodel
from app.business.extension.main import ExtensionBase


class LearnEnglishConfig(sqlmodel.SQLModel): ...


class LearnEnglishState(sqlmodel.SQLModel): ...


class Extension(
    ExtensionBase[LearnEnglishConfig],
    ext_id="learn_english",
    config_cls=LearnEnglishConfig,
):
    @classmethod
    def _init_resolvers(cls):
        from .resolver import LexicalResolver
