import datetime
import typing
import sqlalchemy
import sqlmodel
from typing import Optional as Opt
from .storage import StorageID

ResolverType: typing.TypeAlias = str
"""Type of resolver. 

Extension resolvers should follows `extensions.{extension_id}.{resolver_name}` pattern.
"""
BlockID: typing.TypeAlias = int
ResolverTV = typing.TypeVar("ResolverTV", bound="ResolverType")
"""Resolver type variable"""


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
  storage: Opt[StorageID] = sqlmodel.Field(
    default=None,
    sa_column=sqlalchemy.Column(
      sqlalchemy.Integer,
      sqlalchemy.ForeignKey("storages.id", onupdate="CASCADE", ondelete="SET NULL"),
      nullable=True,
    ),
  )
  resolver: ResolverType = sqlmodel.Field(
    sa_column=sqlalchemy.Column(sqlalchemy.Text, nullable=False)
  )
  content: str = sqlmodel.Field(
    sa_column=sqlalchemy.Column(sqlalchemy.Text, nullable=False)
  )
  """Content of the block.
  
  Block content stored as text in database.
  For runtime usage, use storage to get the raw content.
  """

  async def get_context_as_text(self) -> str:
    from app.business.info_base.resolver import ResolverManager

    resolver = ResolverManager.get(self)
    return await resolver.get_text()
