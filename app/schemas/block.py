import datetime
import typing
import sqlalchemy
import pgvector.sqlalchemy
import sqlmodel
from typing import Optional as Opt
from app.engine import SessionLocal
from .storage import StorageTable, StorageModel

if typing.TYPE_CHECKING:
    from .root import Vector

ResolverType: typing.TypeAlias = str
BlockID: typing.TypeAlias = int


class BlockModel(sqlmodel.SQLModel, table=True):
    __tablename__ = "blocks"  # type: ignore

    id: Opt[BlockID] = sqlmodel.Field(
        sa_column=sqlmodel.Column(sqlmodel.Integer, primary_key=True, autoincrement=True),
        default=None,
    )
    created_at: datetime.datetime = sqlmodel.Field(
        default_factory=datetime.datetime.now,
        sa_column=sqlalchemy.Column(
            sqlalchemy.TIMESTAMP(timezone=True),
            server_default=sqlalchemy.text("CURRENT_TIMESTAMP"),
        ),
    )
    updated_at: datetime.datetime = sqlmodel.Field(
        default_factory=datetime.datetime.now,
        sa_column=sqlalchemy.Column(
            sqlalchemy.TIMESTAMP(timezone=True),
            server_default=sqlalchemy.text("CURRENT_TIMESTAMP"),
            onupdate=datetime.datetime.now,
        ),
    )
    storage: Opt[str] = sqlmodel.Field(
        default=None,
        sa_column=sqlalchemy.Column(sqlalchemy.ForeignKey(StorageTable.name), nullable=True),
    )
    resolver: str = sqlmodel.Field(sa_column=sqlalchemy.Column(sqlalchemy.Text, nullable=False))
    content: str = sqlmodel.Field(sa_column=sqlalchemy.Column(sqlalchemy.Text, nullable=False))

    async def get_context_as_text(self) -> str:
        from app.business.resolver import ResolverManager

        resolver = ResolverManager.new_resolver(self)
        return await resolver.get_text()


class BlockEmbeddingModel(sqlmodel.SQLModel, table=True):
    __tablename__ = "block_embeddings"  # type: ignore

    id: int = sqlmodel.Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.Integer,
            sqlalchemy.ForeignKey("blocks.id", ondelete="CASCADE", onupdate="CASCADE"),
            primary_key=True,
        ),
    )
    embedding: "Vector" = sqlmodel.Field(
        sa_column=sqlalchemy.Column(pgvector.sqlalchemy.VECTOR(1024), nullable=False)
    )
    updated_at: datetime.datetime = sqlmodel.Field(
        default_factory=datetime.datetime.now,
        sa_column=sqlalchemy.Column(
            sqlalchemy.TIMESTAMP(timezone=True), onupdate=datetime.datetime.now
        ),
    )
