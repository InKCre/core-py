__all__ = [
    "SourceCollectJobStatus",
    "SourceCollectJobID",
    "SourceCollectJobModel",
    "SourceCollectJobLogID",
    "SourceCollectJobLogModel",
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


class SourceCollectJobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"


class SourceCollectJobModel(sqlmodel.SQLModel, table=True):
    __tablename__: str = "sources_collect_jobs"  # type: ignore

    id: Opt[SourceCollectJobID] = sqlmodel.Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.Integer, primary_key=True, autoincrement=True
        ),
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
    status: SourceCollectJobStatus = sqlmodel.Field(default=SourceCollectJobStatus.PENDING)
    state: dict = sqlmodel.Field(
        sa_column=sqlalchemy.Column(sqlalchemy.dialects.postgresql.JSONB),
        default_factory=dict,
    )
    config: dict = sqlmodel.Field(
        sa_column=sqlalchemy.Column(sqlalchemy.dialects.postgresql.JSONB),
        default_factory=dict,
    )


SourceCollectJobLogID: typing.TypeAlias = int


class SourceCollectJobLogModel(sqlmodel.SQLModel, table=True):
    __tablename__: str = "sources_collect_jobs_logs"  # type: ignore

    id: Opt[SourceCollectJobLogID] = sqlmodel.Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.BigInteger, primary_key=True, autoincrement=True
        ),
        default=None,
    )
    timestamp: datetime.datetime = sqlmodel.Field(
        default_factory=datetime.datetime.now,
        sa_column=sqlalchemy.Column(sqlalchemy.TIMESTAMP(timezone=True)),
    )
    """Timestamp of the log entry."""
    severity_number: int = sqlmodel.Field(
        sa_column=sqlalchemy.Column(sqlalchemy.SmallInteger),
    )
    """Severity number (following OTel convention)."""
    severity_text: str = sqlmodel.Field(
        sa_column=sqlalchemy.Column(sqlalchemy.Text),
    )
    """Severity text (following OTel convention)."""
    body: str = sqlmodel.Field(
        sa_column=sqlalchemy.Column(sqlalchemy.Text),
    )
    """Log message body."""
    job_id: SourceCollectJobID = sqlmodel.Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.BigInteger,
            sqlalchemy.ForeignKey(
                "sources_collect_jobs.id", onupdate="CASCADE", ondelete="CASCADE"
            ),
        )
    )
    """Reference to the collect job."""
    attributes: dict = sqlmodel.Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.dialects.postgresql.JSONB,
            server_default=sqlalchemy.text("'{}'::jsonb"),
        ),
        default_factory=dict,
    )
    """Custom attributes (JSONB)."""
