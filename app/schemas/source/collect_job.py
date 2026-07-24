__all__ = [
  "SourceCollectJobStatus",
  "SourceCollectJobID",
  "SourceCollectJobModel",
]

import datetime
import enum
import sqlalchemy
import sqlalchemy.dialects.postgresql
import typing
import sqlmodel
from typing import Optional as Opt
from .main import SourceID


SourceCollectJobID: typing.TypeAlias = int


class SourceCollectJobStatus(enum.StrEnum):
  PENDING = "pending"
  RUNNING = "running"
  FINISHED = "finished"
  FAILED = "failed"


class SourceCollectJobModel(sqlmodel.SQLModel, table=True):
  """Model for source collect jobs.

  Source collect jobs should be handled as soon as possible, no schedule given.
  """

  __tablename__: str = "sources_collect_jobs"  # type: ignore

  id: Opt[SourceCollectJobID] = sqlmodel.Field(
    sa_column=sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True),
    default=None,
  )
  source: SourceID = sqlmodel.Field(
    sa_column=sqlalchemy.Column(
      sqlalchemy.Integer,
      sqlalchemy.ForeignKey("sources.id", onupdate="CASCADE", ondelete="CASCADE"),
    )
  )
  created_at: datetime.datetime = sqlmodel.Field(
    default_factory=datetime.datetime.now,
    sa_column=sqlalchemy.Column(
      sqlalchemy.TIMESTAMP(timezone=True), onupdate=datetime.datetime.now
    ),
  )
  started_at: Opt[datetime.datetime] = sqlmodel.Field(
    default=None,
    sa_column=sqlalchemy.Column(sqlalchemy.TIMESTAMP(timezone=True), nullable=True),
  )
  closed_at: Opt[datetime.datetime] = sqlmodel.Field(
    default=None,
    sa_column=sqlalchemy.Column(sqlalchemy.TIMESTAMP(timezone=True), nullable=True),
  )
  """When this collect job is finished/failed.
    """
  status: SourceCollectJobStatus = sqlmodel.Field(
    default=SourceCollectJobStatus.PENDING,
    sa_column=sqlalchemy.Column(
      sqlalchemy.Enum(
        SourceCollectJobStatus,
        values_callable=lambda x: [e.value for e in x],
        inherit_schema=True,
      ),
      server_default=SourceCollectJobStatus.PENDING,
      nullable=False,
    ),
  )
  state: dict = sqlmodel.Field(
    sa_column=sqlalchemy.Column(sqlalchemy.dialects.postgresql.JSONB),
    default_factory=dict,
  )
  config: dict = sqlmodel.Field(
    sa_column=sqlalchemy.Column(sqlalchemy.dialects.postgresql.JSONB),
    default_factory=dict,
  )
