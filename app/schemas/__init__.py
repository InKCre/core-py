__all__ = [
  "Base",
  "BlockModel",
  "StorageModel",
  "StorageBlobModel",
  "StorageTypesModel",
  "RelationModel",
  "SourceModel",
  "SourceCollectJobModel",
  "ExtensionModel",
  "RelationEmbeddingModel",
  "BlockEmbeddingModel",
  "ClientModel",
]

import sqlalchemy.orm
import sqlmodel

from app.database_contract import PROTOCOL_SCHEMA


Base = sqlalchemy.orm.declarative_base(metadata=sqlalchemy.MetaData(schema=PROTOCOL_SCHEMA))
sqlmodel.SQLModel.metadata = Base.metadata

from .info_base.block import BlockModel
from .info_base.storage import StorageBlobModel, StorageModel, StorageTypesModel
from .info_base.relation import RelationModel
from .source import SourceModel, SourceCollectJobModel
from .extension.main import ExtensionModel
from .sink import RelationEmbeddingModel, BlockEmbeddingModel
from .client.main import ClientModel
