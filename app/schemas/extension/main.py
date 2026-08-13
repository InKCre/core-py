import typing
import uuid

import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlmodel


ExtensionName: typing.TypeAlias = str
EXTENSION_NAME_PATTERN = (
  r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?/"
  r"[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$"
)
EXTENSION_SEMVER_PATTERN = (
  r"^(0|[1-9][0-9]*)[.](0|[1-9][0-9]*)[.](0|[1-9][0-9]*)"
  r"(-(0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
  r"([.](0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?$"
)


class ExtensionModel(sqlmodel.SQLModel, table=True):
  """Private persistence model for one exact deployment Extension Release."""

  __tablename__: str = "extensions"  # type: ignore
  __table_args__ = (
    sqlalchemy.CheckConstraint(
      f"name ~ '{EXTENSION_NAME_PATTERN}'",
      name="extensions_name_canonical",
    ),
    sqlalchemy.CheckConstraint(
      f"version ~ '{EXTENSION_SEMVER_PATTERN}'",
      name="extensions_version_canonical",
    ),
    sqlalchemy.CheckConstraint(
      "jsonb_typeof(state) = 'object'",
      name="extensions_state_object",
    ),
  )

  name: ExtensionName = sqlmodel.Field(
    sa_column=sqlalchemy.Column(sqlalchemy.Text, primary_key=True)
  )
  version: str = sqlmodel.Field(
    sa_column=sqlalchemy.Column(sqlalchemy.Text, nullable=False)
  )
  enabled: list[uuid.UUID] = sqlmodel.Field(
    default_factory=list,
    sa_column=sqlalchemy.Column(
      sqlalchemy.dialects.postgresql.ARRAY(
        sqlalchemy.dialects.postgresql.UUID(as_uuid=True)
      ),
      server_default=sqlalchemy.text("'{}'::uuid[]"),
      nullable=False,
    ),
  )
  nickname: str | None = sqlmodel.Field(
    default=None,
    sa_column=sqlalchemy.Column(sqlalchemy.Text, nullable=True),
  )
  config: dict = sqlmodel.Field(
    default_factory=dict,
    sa_column=sqlalchemy.Column(
      sqlalchemy.dialects.postgresql.JSONB,
      server_default=sqlalchemy.text("'{}'::jsonb"),
      nullable=False,
    ),
  )
  state: dict = sqlmodel.Field(
    default_factory=dict,
    sa_column=sqlalchemy.Column(
      sqlalchemy.dialects.postgresql.JSONB,
      server_default=sqlalchemy.text("'{}'::jsonb"),
      nullable=False,
    ),
  )
  config_schema: dict | None = sqlmodel.Field(
    default=None,
    sa_column=sqlalchemy.Column(
      sqlalchemy.dialects.postgresql.JSONB,
      nullable=True,
    ),
  )
