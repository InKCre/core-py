import enum
import typing
import aiohttp
import pydantic
import sqlalchemy
from . import Base
from utils.base import enum_serializer, AIOHTTP_CONNECTOR_GETTER


StorageType: typing.TypeAlias = str


class StorageTable(Base):
    __tablename__ = "storages"

    name = sqlalchemy.Column(sqlalchemy.Text, primary_key=True, nullable=False)
    nickname = sqlalchemy.Column(sqlalchemy.Text, nullable=True, default=None)
    type = sqlalchemy.Column(
        nullable=False,
    )


class StorageModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    name: str
    nickname: str | None = None
    type: typing.Annotated[StorageType, enum_serializer]
