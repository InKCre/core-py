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

from .info_base.block import BlockModel
from .info_base.storage import StorageModel, StorageTypesModel
from .info_base.relation import RelationModel
from .source import SourceModel, SourceCollectJobModel
from .extension.main import ExtensionModel
