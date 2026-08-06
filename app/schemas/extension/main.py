import uuid
import pydantic
import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlmodel
import typing
from typing import Optional as Opt


ExtensionID: typing.TypeAlias = str


class EnableExtensionCommand(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  action: typing.Literal["enable"]
  extension: ExtensionID


class DisableExtensionCommand(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  action: typing.Literal["disable"]
  extension: ExtensionID


class PatchExtensionConfigCommand(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  action: typing.Literal["patch_config"]
  extension: ExtensionID
  patch: dict[str, typing.Any]


ExtensionManagementCommand: typing.TypeAlias = typing.Annotated[
  EnableExtensionCommand | DisableExtensionCommand | PatchExtensionConfigCommand,
  pydantic.Field(discriminator="action"),
]


class ExtensionModel(sqlmodel.SQLModel, table=True):
  """

  Globally, every extension has a unique ID.
  Only one instance of each extension on a deployment.
  If a record presents here, the extension is installed.
  """

  __tablename__: str = "extensions"  # type: ignore

  id: ExtensionID = sqlmodel.Field(
    sa_column=sqlalchemy.Column(sqlalchemy.Text, primary_key=True)
  )
  version: str = sqlmodel.Field(sa_column=sqlmodel.Column(sqlmodel.Text, nullable=False))
  """Version of extension.
    
    format: `major.minor.patch`.
    """
  enabled: list[uuid.UUID] = sqlmodel.Field(
    default_factory=list,
    sa_column=sqlmodel.Column(
      sqlalchemy.dialects.postgresql.ARRAY(
        sqlalchemy.dialects.postgresql.UUID(as_uuid=True)
      ),
      server_default=sqlalchemy.text("'{}'::uuid[]"),
      nullable=False,
    ),
  )
  """List of Peer IDs for which this extension is enabled.

  Empty array means disabled for all Peers.
  """
  nickname: Opt[str] = sqlmodel.Field(
    default=None,
    sa_column=sqlalchemy.Column(sqlalchemy.Text, nullable=True),
  )
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
