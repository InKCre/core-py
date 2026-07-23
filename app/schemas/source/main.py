__all__ = [
  "CollectAt",
  "SourceID",
  "SourceModel",
  "SourceTypesModel",
]

import apscheduler.triggers.cron
import sqlalchemy
import typing
import sqlalchemy.dialects
import sqlalchemy.dialects.postgresql
import sqlmodel
from typing import Optional as Opt


SourceID: typing.TypeAlias = int


class CollectAt(sqlmodel.SQLModel):
  day_of_week: Opt[int] = sqlmodel.Field(default=None, ge=0, le=6)
  """0-6, where 0 is Monday

    None means run every day.
    """
  hour: int = sqlmodel.Field(default=0, ge=0, le=23)
  minute: int = sqlmodel.Field(default=0, ge=0, le=59)

  def to_trigger(self) -> apscheduler.triggers.cron.CronTrigger:
    return apscheduler.triggers.cron.CronTrigger(
      day_of_week=self.day_of_week,
      hour=self.hour,
      minute=self.minute,
    )


class CollectAtType(sqlmodel.TypeDecorator):
  impl = sqlalchemy.dialects.postgresql.JSONB

  def process_bind_param(self, value, dialect):
    return value.model_dump() if isinstance(value, CollectAt) else value

  def process_result_value(self, value, dialect):
    return CollectAt.model_validate(value) if value else None


class SourceTypesModel(sqlmodel.SQLModel, table=True):
  __tablename__: str = "sources_types"  # type: ignore

  id: str = sqlmodel.Field(sa_column=sqlalchemy.Column(sqlalchemy.Text, primary_key=True))
  """Type of source.
    
    An absolute import path to the module where souce class at.
    """
  description: str = sqlmodel.Field(sa_column=sqlalchemy.Column(sqlalchemy.Text))
  """Description of this source type."""
  config_schema: dict = sqlmodel.Field(
    sa_column=sqlalchemy.Column(
      sqlalchemy.dialects.postgresql.JSONB,
      server_default=sqlalchemy.text("'{}'::jsonb"),
    ),
    default=dict,
  )


class SourceModel(sqlmodel.SQLModel, table=True):
  __tablename__: str = "sources"  # type: ignore

  id: Opt[SourceID] = sqlmodel.Field(
    sa_column=sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True),
    default=None,
  )
  type: str = sqlmodel.Field(
    sa_column=sqlalchemy.Column(
      sqlalchemy.Text,
      sqlalchemy.ForeignKey("sources_types.id", onupdate="CASCADE", ondelete="CASCADE"),
    )
  )
  """Type of source.
    
    An absolute import path to the module where souce class at.
    When delete a source type, all sources of this type will be deleted too.
    """
  nickname: Opt[str] = sqlmodel.Field(
    default=None,
    sa_column=sqlalchemy.Column(sqlalchemy.Text, nullable=True),
  )
  config: dict = sqlmodel.Field(
    sa_column=sqlalchemy.Column(
      sqlalchemy.dialects.postgresql.JSONB,
      server_default=sqlalchemy.text("'{}'::jsonb"),
    ),
    default=dict,
  )
  collect_at: Opt[CollectAt] = sqlmodel.Field(
    sa_column=sqlalchemy.Column(CollectAtType),
    default=None,
  )
  """When to run collect method of this source.

    None for disabled.
    """
  state: dict = sqlmodel.Field(
    sa_column=sqlalchemy.Column(
      sqlalchemy.dialects.postgresql.JSONB,
      server_default=sqlalchemy.text("'{}'::jsonb"),
    ),
    default_factory=dict,
  )
  """Store source-specific state (e.g., last_uid for mail,
    latest_tweet_id for twitter)."""
