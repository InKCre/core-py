import datetime
import typing
import sqlalchemy
import pgvector.sqlalchemy
import sqlmodel

if typing.TYPE_CHECKING:
  from app.schemas.info_base.main import Vector


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
