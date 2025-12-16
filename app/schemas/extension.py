import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlmodel
import typing
from typing import Optional as Opt


ExtensionID: typing.TypeAlias = str


class ExtensionModel(sqlmodel.SQLModel, table=True):
    """

    Globally, every extension has a unique ID.
    Only one instance of each extension on a deployment.
    If a record presents here, the extension is installed.
    """

    __tablename__: str = "extensions"  # type: ignore

    id: ExtensionID = sqlmodel.Field(primary_key=True)
    version: str = sqlmodel.Field(sa_column=sqlmodel.Column(sqlmodel.Text, nullable=False))
    """Version of extension.
    
    format: `major.minor.patch`.
    """
    disabled: bool = sqlmodel.Field(default=False)
    nickname: Opt[str] = sqlmodel.Field(default=None)
    config: dict = sqlmodel.Field(
        default_factory=dict,
        sa_column=sqlmodel.Column(
            sqlalchemy.dialects.postgresql.JSONB,
            server_default=sqlalchemy.text("'{}'::jsonb"),
        ),
    )
    config_schema: Opt[dict] = sqlmodel.Field(
        default=None, sa_column=sqlmodel.Column(sqlalchemy.dialects.postgresql.JSONB)
    )
    """JSON schema for the config field.
    
    Auto-populated from config_cls.model_json_schema().
    """
