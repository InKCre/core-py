__all__ = [
    "Base",
    "BlockModel",
    "StorageModel",
    "StorageTypesModel",
    "RelationModel",
    "SourceModel",
    "SourceCollectJobModel",
    "ExtensionModel",
]

import sqlalchemy.orm
import sqlmodel

Base = sqlalchemy.orm.declarative_base()
sqlmodel.SQLModel.metadata = Base.metadata

from .block import BlockModel
from .storage import StorageModel, StorageTypesModel
from .relation import RelationModel
from .source import SourceModel, SourceCollectJobModel
from .extension import ExtensionModel
