import uuid

import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlmodel


REGISTRY_COORDINATE_SEGMENT_PATTERN = r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$"
REGISTRY_SEMVER_PATTERN = (
  r"^(0|[1-9][0-9]*)[.](0|[1-9][0-9]*)[.](0|[1-9][0-9]*)"
  r"(-(0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
  r"([.](0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?$"
)
REGISTRY_TARGET_KEY_PATTERN = r"^[a-z0-9]([a-z0-9._-]{0,126}[a-z0-9])?$"
REGISTRY_TARGET_DIGEST_PATTERN = r"^sha256:[0-9a-f]{64}$"


class ExtensionInstallationModel(sqlmodel.SQLModel, table=True):
  """One deployment-wide exact Registry Extension Version installation."""

  __tablename__: str = "extension_installations"  # type: ignore
  __table_args__ = (
    sqlalchemy.CheckConstraint(
      f"namespace ~ '{REGISTRY_COORDINATE_SEGMENT_PATTERN}'",
      name="extension_installations_namespace_canonical",
    ),
    sqlalchemy.CheckConstraint(
      f"name ~ '{REGISTRY_COORDINATE_SEGMENT_PATTERN}'",
      name="extension_installations_name_canonical",
    ),
    sqlalchemy.CheckConstraint(
      f"version ~ '{REGISTRY_SEMVER_PATTERN}'",
      name="extension_installations_version_canonical",
    ),
    sqlalchemy.UniqueConstraint(
      "namespace",
      "name",
      "version",
      name="extension_installations_coordinate_version_key",
    ),
  )

  namespace: str = sqlmodel.Field(
    sa_column=sqlalchemy.Column(sqlalchemy.Text, primary_key=True)
  )
  name: str = sqlmodel.Field(sa_column=sqlalchemy.Column(sqlalchemy.Text, primary_key=True))
  version: str = sqlmodel.Field(
    sa_column=sqlalchemy.Column(sqlalchemy.Text, nullable=False)
  )
  config: dict = sqlmodel.Field(
    default_factory=dict,
    sa_column=sqlalchemy.Column(
      sqlalchemy.dialects.postgresql.JSONB,
      server_default=sqlalchemy.text("'{}'::jsonb"),
      nullable=False,
    ),
  )
  config_schema: dict = sqlmodel.Field(
    default_factory=dict,
    sa_column=sqlalchemy.Column(
      sqlalchemy.dialects.postgresql.JSONB,
      server_default=sqlalchemy.text("'{}'::jsonb"),
      nullable=False,
    ),
  )


class ExtensionPeerBindingModel(sqlmodel.SQLModel, table=True):
  """One exact admitted Registry target enabled for one deployment peer."""

  __tablename__: str = "extension_peer_bindings"  # type: ignore
  __table_args__ = (
    sqlalchemy.CheckConstraint(
      f"namespace ~ '{REGISTRY_COORDINATE_SEGMENT_PATTERN}'",
      name="extension_peer_bindings_namespace_canonical",
    ),
    sqlalchemy.CheckConstraint(
      f"name ~ '{REGISTRY_COORDINATE_SEGMENT_PATTERN}'",
      name="extension_peer_bindings_name_canonical",
    ),
    sqlalchemy.CheckConstraint(
      f"version ~ '{REGISTRY_SEMVER_PATTERN}'",
      name="extension_peer_bindings_version_canonical",
    ),
    sqlalchemy.CheckConstraint(
      f"target_key ~ '{REGISTRY_TARGET_KEY_PATTERN}'",
      name="extension_peer_bindings_target_key_canonical",
    ),
    sqlalchemy.CheckConstraint(
      f"target_digest ~ '{REGISTRY_TARGET_DIGEST_PATTERN}'",
      name="extension_peer_bindings_target_digest_canonical",
    ),
    sqlalchemy.ForeignKeyConstraint(
      ["namespace", "name", "version"],
      [
        "extension_installations.namespace",
        "extension_installations.name",
        "extension_installations.version",
      ],
      name="extension_peer_bindings_installation_fkey",
      ondelete="RESTRICT",
      deferrable=True,
      initially="DEFERRED",
    ),
    sqlalchemy.ForeignKeyConstraint(
      ["peer_id"],
      ["clients.id"],
      name="extension_peer_bindings_peer_fkey",
      ondelete="RESTRICT",
    ),
  )

  namespace: str = sqlmodel.Field(
    sa_column=sqlalchemy.Column(sqlalchemy.Text, primary_key=True)
  )
  name: str = sqlmodel.Field(sa_column=sqlalchemy.Column(sqlalchemy.Text, primary_key=True))
  version: str = sqlmodel.Field(
    sa_column=sqlalchemy.Column(sqlalchemy.Text, nullable=False)
  )
  peer_id: uuid.UUID = sqlmodel.Field(
    sa_column=sqlalchemy.Column(
      sqlalchemy.dialects.postgresql.UUID(as_uuid=True),
      primary_key=True,
    )
  )
  target_key: str = sqlmodel.Field(
    sa_column=sqlalchemy.Column(sqlalchemy.Text, nullable=False)
  )
  target_digest: str = sqlmodel.Field(
    sa_column=sqlalchemy.Column(sqlalchemy.Text, nullable=False)
  )
