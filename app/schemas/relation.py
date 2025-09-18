import dataclasses
import typing
from typing import Optional as Opt
import datetime
import sqlalchemy
import pgvector.sqlalchemy
import sqlmodel

if typing.TYPE_CHECKING:
    from .root import Vector

RelationID: typing.TypeAlias = int


class RelationModel(sqlmodel.SQLModel, table=True):
    __tablename__ = "relations"  # type: ignore

    id: Opt[RelationID] = sqlmodel.Field(
        sa_column=sqlmodel.Column(sqlmodel.Integer, primary_key=True, autoincrement=True),
        default=None,
    )
    updated_at: datetime.datetime = sqlmodel.Field(
        default_factory=datetime.datetime.now,
        sa_column=sqlalchemy.Column(
            sqlalchemy.TIMESTAMP(timezone=True),
            onupdate=datetime.datetime.now,
            server_default=sqlalchemy.text("CURRENT_TIMESTAMP"),
        ),
    )
    from_: int = sqlmodel.Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.Integer,
            sqlalchemy.ForeignKey("blocks.id", ondelete="CASCADE", onupdate="CASCADE"),
        ),
        default=0,
    )
    to_: int = sqlmodel.Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.Integer,
            sqlalchemy.ForeignKey("blocks.id", ondelete="CASCADE", onupdate="CASCADE"),
        ),
        default=0,
    )
    content: str = sqlmodel.Field(sa_column=sqlalchemy.Column(sqlalchemy.Text, nullable=False))


class RelationEmbeddingModel(sqlmodel.SQLModel, table=True):
    __tablename__ = "relation_embeddings"  # type: ignore

    id: int = sqlmodel.Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.Integer,
            sqlalchemy.ForeignKey("relations.id", ondelete="CASCADE", onupdate="CASCADE"),
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
