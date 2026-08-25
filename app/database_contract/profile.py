"""Checked-in built-in catalog profile.

The profile is data only. Reconciliation can consume it without importing FastAPI,
application settings, extension runtimes, or the scheduler.
"""

from dataclasses import dataclass
from typing import Any


JsonObject = dict[str, Any]


@dataclass(frozen=True)
class TypeProfile:
  id: str
  description: str
  config_schema: JsonObject


@dataclass(frozen=True)
class StorageTypeProfile:
  id: str
  description: str
  config_schema: JsonObject
  writable: bool


@dataclass(frozen=True)
class JobTypeProfile:
  id: str
  description: str
  parameters_schema: JsonObject
  default_timeout_seconds: int


@dataclass(frozen=True)
class StorageProfile:
  id: int
  type: str
  nickname: str
  config: JsonObject


def _object_schema(
  title: str,
  description: str,
  properties: JsonObject,
) -> JsonObject:
  return {
    "description": description,
    "properties": properties,
    "title": title,
    "type": "object",
  }


def _positive_integer(default: int) -> JsonObject:
  return {"default": default, "exclusiveMinimum": 0, "type": "integer"}


def _boolean(default: bool) -> JsonObject:
  return {"default": default, "type": "boolean"}


HTTP_STORAGE_SCHEMA = _object_schema(
  "HTTPStorageConfig",
  "Configuration for HTTP storage.",
  {
    "follow_redirects": _boolean(True),
    "max_response_bytes": _positive_integer(64 * 1024 * 1024),
    "timeout": _positive_integer(30),
  },
)

OPENAI_COMPATIBLE_DIALECT_SCHEMA = {
  "additionalProperties": False,
  "description": "Connection values for one OpenAI-compatible provider instance.",
  "properties": {
    "api_key": {
      "minLength": 1,
      "title": "Api Key",
      "type": "string",
    },
    "base_url": {
      "anyOf": [
        {"minLength": 1, "type": "string"},
        {"type": "null"},
      ],
      "default": None,
      "title": "Base Url",
    },
  },
  "required": ["api_key"],
  "title": "OpenAICompatibleConfig",
  "type": "object",
}

BUILTIN_AI_DIALECTS = (
  TypeProfile(
    "core.openai-compatible.v1",
    "OpenAI-compatible embedding and chat protocol.",
    OPENAI_COMPATIBLE_DIALECT_SCHEMA,
  ),
  TypeProfile(
    "core.alibaba-model-studio.v1",
    "Alibaba Model Studio OpenAI-compatible multimodal chat protocol.",
    OPENAI_COMPATIBLE_DIALECT_SCHEMA,
  ),
)

BUILTIN_STORAGE_TYPES = (
  StorageTypeProfile(
    "http",
    "HTTP storage for bounded retrieval of opaque response bytes.",
    HTTP_STORAGE_SCHEMA,
    False,
  ),
)

BUILTIN_STORAGE_TYPES += (
  StorageTypeProfile(
    "postgresql_binary",
    "PostgreSQL storage for deployment-owned binary content.",
    _object_schema(
      "PostgreSQLBinaryStorageConfig",
      "Configuration for PostgreSQL binary storage.",
      {},
    ),
    True,
  ),
)


SOURCE_COLLECT_PARAMETERS_SCHEMA = {
  "additionalProperties": False,
  "description": "Parameters of the exact ordinary Source Job type.",
  "properties": {
    "config": {
      "additionalProperties": True,
      "title": "Config",
      "type": "object",
    },
    "source": {"title": "Source", "type": "integer"},
  },
  "required": ["source"],
  "title": "SourceCollectParameters",
  "type": "object",
}

SOURCE_BACKFILL_PARAMETERS_SCHEMA = {
  **SOURCE_COLLECT_PARAMETERS_SCHEMA,
  "description": "Parameters of the exact historical Source Job type.",
  "title": "SourceBackfillParameters",
}

LEXICAL_MAINTENANCE_PARAMETERS_SCHEMA = {
  "$defs": {
    "LexicalMaintenanceOptions": {
      "additionalProperties": False,
      "properties": {
        "diagnostic_limit": {
          "default": 20,
          "minimum": 0,
          "title": "Diagnostic Limit",
          "type": "integer",
        },
        "max_records": {
          "default": 100,
          "minimum": 1,
          "title": "Max Records",
          "type": "integer",
        },
        "scan_page_size": {
          "default": 100,
          "minimum": 1,
          "title": "Scan Page Size",
          "type": "integer",
        },
      },
      "title": "LexicalMaintenanceOptions",
      "type": "object",
    }
  },
  "additionalProperties": False,
  "properties": {
    "options": {"$ref": "#/$defs/LexicalMaintenanceOptions"},
  },
  "title": "LexicalMaintenanceJobParameters",
  "type": "object",
}

SEMANTIC_MAINTENANCE_PARAMETERS_SCHEMA = {
  "$defs": {
    "EmbeddingMaintenanceOptions": {
      "additionalProperties": False,
      "description": "Peer-local bounds for one resumable maintenance invocation.",
      "properties": {
        "batch_size": {
          "default": 20,
          "minimum": 1,
          "title": "Batch Size",
          "type": "integer",
        },
        "diagnostic_limit": {
          "default": 20,
          "minimum": 0,
          "title": "Diagnostic Limit",
          "type": "integer",
        },
        "max_embeddings": {
          "default": 100,
          "minimum": 1,
          "title": "Max Embeddings",
          "type": "integer",
        },
        "scan_page_size": {
          "default": 100,
          "minimum": 1,
          "title": "Scan Page Size",
          "type": "integer",
        },
      },
      "title": "EmbeddingMaintenanceOptions",
      "type": "object",
    }
  },
  "additionalProperties": False,
  "properties": {
    "options": {"$ref": "#/$defs/EmbeddingMaintenanceOptions"},
    "profile": {
      "anyOf": [{"type": "integer"}, {"type": "null"}],
      "default": None,
      "title": "Profile",
    },
  },
  "title": "EmbeddingMaintenanceJobParameters",
  "type": "object",
}

MEDIA_INTERPRETATION_PARAMETERS_SCHEMA = {
  "additionalProperties": False,
  "properties": {},
  "title": "MediaInterpretationJobParameters",
  "type": "object",
}

BUILTIN_JOB_TYPES = (
  JobTypeProfile(
    "core.source.collect.v1",
    "Run one ordinary collection command for a configured Source.",
    SOURCE_COLLECT_PARAMETERS_SCHEMA,
    300,
  ),
  JobTypeProfile(
    "core.source.backfill.v1",
    "Run one exact historical collection command for a configured Source.",
    SOURCE_BACKFILL_PARAMETERS_SCHEMA,
    1800,
  ),
  JobTypeProfile(
    "core.feature_retrieval.lexical.maintain.v1",
    "Maintain missing or stale Block lexical projection records.",
    LEXICAL_MAINTENANCE_PARAMETERS_SCHEMA,
    900,
  ),
  JobTypeProfile(
    "core.feature_retrieval.lexical.rebuild.v1",
    "Rebuild Block lexical records present before invocation.",
    LEXICAL_MAINTENANCE_PARAMETERS_SCHEMA,
    1800,
  ),
  JobTypeProfile(
    "core.semantic_retrieval.maintain.v1",
    "Maintain missing or stale semantic embedding records.",
    SEMANTIC_MAINTENANCE_PARAMETERS_SCHEMA,
    900,
  ),
  JobTypeProfile(
    "core.semantic_retrieval.rebuild.v1",
    "Rebuild semantic embedding records present before invocation.",
    SEMANTIC_MAINTENANCE_PARAMETERS_SCHEMA,
    1800,
  ),
  JobTypeProfile(
    "core.organization.media_interpretation.v1",
    "Interpret missing image, audio, and video Blocks through configured Agents.",
    MEDIA_INTERPRETATION_PARAMETERS_SCHEMA,
    1800,
  ),
)


BUILTIN_STORAGES = (
  StorageProfile(-1, "http", "HTTP", {}),
  StorageProfile(-4, "postgresql_binary", "PostgreSQL Binary", {}),
)

BUILTIN_AI_DIALECTS_BY_ID = {item.id: item for item in BUILTIN_AI_DIALECTS}
BUILTIN_STORAGE_TYPES_BY_ID = {item.id: item for item in BUILTIN_STORAGE_TYPES}
BUILTIN_JOB_TYPES_BY_ID = {item.id: item for item in BUILTIN_JOB_TYPES}
