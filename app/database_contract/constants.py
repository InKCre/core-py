"""Stable names and values shared by migrations, runtimes, and consumers."""

import uuid


CONTRACT_FORMAT = 1
CONTRACT_REVISION = "peer-database-runtime-v1"

PROTOCOL_SCHEMA = "inkcre"
INTERNAL_SCHEMA = "inkcre_internal"

AUTHENTICATED_ROLE = "authenticated"
AUTHENTICATOR_ROLE = "authenticator"
ANONYMOUS_ROLE = "anonymous"
CORE_RUNTIME_ROLE = "inkcre_core"

JWT_ALGORITHM = "HS256"
JWT_ROLE = AUTHENTICATED_ROLE
JWT_ISSUER = "inkcre-client"
JWT_AUDIENCE = "inkcre-api"
JWT_MAX_LIFETIME_SECONDS = 24 * 60 * 60
JWT_MINIMUM_SECRET_BYTES = 32

DEVELOPMENT_CLIENT_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
DEVELOPMENT_CLIENT_NAME = "client-web-development"

DATABASE_ENVIRONMENTS = frozenset({"runtime", "development", "preview", "production"})
RESET_CONFIRMATION = "reset-development-data"

APPLICATION_TABLES = (
  "block_embeddings",
  "blocks",
  "clients",
  "extensions",
  "logs",
  "relation_embeddings",
  "relations",
  "sources",
  "sources_collect_jobs",
  "sources_types",
  "storage_types",
  "storage_blobs",
  "storages",
)
