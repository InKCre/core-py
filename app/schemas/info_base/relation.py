import typing
from typing import Optional as Opt
import datetime
import sqlalchemy
import sqlmodel

from app.schemas.info_base.block import BlockID

RelationID: typing.TypeAlias = int


class RelationForm(sqlmodel.SQLModel):
  """Producer-owned values for creating one Relation."""

  model_config = {"extra": "forbid"}

  content: str = sqlmodel.Field(
    sa_column=sqlalchemy.Column(sqlalchemy.Text, nullable=False)
  )


class RelationCreateForm(RelationForm):
  """Standalone Relation creation command with persisted Block endpoints."""

  from_: BlockID
  to_: BlockID


class RelationModel(RelationForm, table=True):
  __tablename__ = "relations"  # type: ignore

  id: Opt[RelationID] = sqlmodel.Field(
    sa_column=sqlmodel.Column(sqlmodel.Integer, primary_key=True, autoincrement=True),
    default=None,
  )
  updated_at: datetime.datetime = sqlmodel.Field(
    default=None,
    sa_column=sqlalchemy.Column(
      sqlalchemy.TIMESTAMP(timezone=True),
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
