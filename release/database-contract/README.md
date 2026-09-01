# Generated database contract

The protected-main release workflow initializes a separate neutral runtime database, then exports
`database-roles.sql`, `database-schema.sql`, `runtime-contract.json`, and `manifest.json` into this
directory before the canonical service image is built. The schema contains the whole database
definition plus only the Alembic and contract-state rows required to resume the lifecycle; it
contains no application data. Source checkouts contain only this marker, and release publication
fails unless all four generated files are present and valid.
