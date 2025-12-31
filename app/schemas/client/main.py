import datetime
import uuid
import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlmodel
import typing
from typing import Optional as Opt


ClientID: typing.TypeAlias = uuid.UUID


class ClientModel(sqlmodel.SQLModel, table=True):
    """Client registration model.

    Represents a client instance that connects to this InKCre deployment.
    All clients are equal peers in the network.
    """

    __tablename__: str = "clients"  # type: ignore

    id: ClientID = sqlmodel.Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
        )
    )
    name: str = sqlmodel.Field(
        sa_column=sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    )
    labels: list[str] = sqlmodel.Field(
        default_factory=list,
        sa_column=sqlalchemy.Column(
            sqlalchemy.dialects.postgresql.ARRAY(sqlalchemy.Text),
            server_default=sqlalchemy.text("'{}'::text[]"),
        ),
    )
    rest_api_url: Opt[str] = sqlmodel.Field(
        default=None,
        sa_column=sqlalchemy.Column(sqlalchemy.Text, nullable=True),
    )
    """REST API base URL. Nullable since not all clients are reachable (e.g., client-web)."""
    created_at: datetime.datetime = sqlmodel.Field(
        default_factory=datetime.datetime.now,
        sa_column=sqlalchemy.Column(
            sqlalchemy.TIMESTAMP(timezone=True),
            server_default=sqlalchemy.text("CURRENT_TIMESTAMP"),
        ),
    )
