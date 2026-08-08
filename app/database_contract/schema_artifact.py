"""Neutral PostgreSQL schema artifact carried by canonical service images."""

from hashlib import sha256
import json
import os
from pathlib import Path
import re
from typing import Any

from .constants import CONTRACT_REVISION


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ARTIFACT_ROOT = PROJECT_ROOT / "database-contract"
SCHEMA_FILE_NAME = "database-schema.sql"
ROLES_FILE_NAME = "database-roles.sql"
MANIFEST_FILE_NAME = "manifest.json"
RUNTIME_CONTRACT_FILE_NAME = "runtime-contract.json"
SCHEMA_ARTIFACT_FORMAT = 1
SOURCE_REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def _read_json_object(path: Path) -> dict[str, Any]:
  document = json.loads(path.read_text())
  if not isinstance(document, dict):
    raise ValueError(f"{path.name} must contain a JSON object")
  return document


def _artifact_digest(path: Path) -> str:
  content = path.read_bytes()
  if not content.strip():
    raise ValueError(f"{path.name} must not be empty")
  return sha256(content).hexdigest()


def _file_metadata(path: Path, image_path: str) -> dict[str, object]:
  return {
    "path": image_path,
    "sha256": _artifact_digest(path),
    "size": path.stat().st_size,
  }


def create_schema_manifest(
  schema_path: Path,
  roles_path: Path,
  runtime_contract_path: Path,
  source_revision: str,
) -> dict[str, Any]:
  """Bind a database dump to the exact runtime contract that produced it."""
  if SOURCE_REVISION_PATTERN.fullmatch(source_revision) is None:
    raise ValueError("source revision must be a 40-character lowercase commit SHA")

  runtime_contract = _read_json_object(runtime_contract_path)
  if runtime_contract.get("source_revision") != source_revision:
    raise ValueError("runtime contract source revision does not match the release")

  contract_revision = runtime_contract.get("revision")
  if not isinstance(contract_revision, str) or not contract_revision:
    raise ValueError("runtime contract revision must be a non-empty string")

  return {
    "format": SCHEMA_ARTIFACT_FORMAT,
    "contract_revision": contract_revision,
    "source_revision": source_revision,
    "schema": _file_metadata(
      schema_path,
      f"/app/database-contract/{SCHEMA_FILE_NAME}",
    ),
    "roles": _file_metadata(
      roles_path,
      f"/app/database-contract/{ROLES_FILE_NAME}",
    ),
    "runtime_contract": _file_metadata(
      runtime_contract_path,
      f"/app/database-contract/{RUNTIME_CONTRACT_FILE_NAME}",
    ),
  }


def write_schema_manifest(
  schema_path: Path,
  roles_path: Path,
  runtime_contract_path: Path,
  output_path: Path,
  source_revision: str,
) -> None:
  manifest = create_schema_manifest(
    schema_path,
    roles_path,
    runtime_contract_path,
    source_revision,
  )
  output_path.write_text(f"{json.dumps(manifest, indent=2, sort_keys=True)}\n")


def read_schema_manifest(
  artifact_root: Path = SCHEMA_ARTIFACT_ROOT,
) -> dict[str, Any]:
  """Verify and return the schema evidence embedded in this service image."""
  manifest = _read_json_object(artifact_root / MANIFEST_FILE_NAME)
  if manifest.get("format") != SCHEMA_ARTIFACT_FORMAT:
    raise ValueError("unsupported database schema artifact format")
  if manifest.get("contract_revision") != CONTRACT_REVISION:
    raise ValueError("database schema artifact contract revision does not match runtime")

  source_revision = manifest.get("source_revision")
  if not isinstance(source_revision, str):
    raise ValueError("database schema artifact source revision is missing")
  if SOURCE_REVISION_PATTERN.fullmatch(source_revision) is None:
    raise ValueError("database schema artifact source revision is invalid")
  runtime_source_revision = os.getenv("INKCRE_SOURCE_REVISION", "unknown")
  if runtime_source_revision not in {"unknown", source_revision}:
    raise ValueError("database schema artifact source revision does not match runtime")

  schema = manifest.get("schema")
  if not isinstance(schema, dict):
    raise ValueError("database schema artifact metadata is missing")
  schema_path = artifact_root / SCHEMA_FILE_NAME
  if schema.get("path") != f"/app/database-contract/{SCHEMA_FILE_NAME}":
    raise ValueError("database schema artifact path is invalid")
  if schema.get("sha256") != _artifact_digest(schema_path):
    raise ValueError("database schema artifact digest does not match its manifest")
  if schema.get("size") != schema_path.stat().st_size:
    raise ValueError("database schema artifact size does not match its manifest")

  roles = manifest.get("roles")
  if not isinstance(roles, dict):
    raise ValueError("database role artifact metadata is missing")
  roles_path = artifact_root / ROLES_FILE_NAME
  if roles.get("path") != f"/app/database-contract/{ROLES_FILE_NAME}":
    raise ValueError("database role artifact path is invalid")
  if roles.get("sha256") != _artifact_digest(roles_path):
    raise ValueError("database role artifact digest does not match its manifest")
  if roles.get("size") != roles_path.stat().st_size:
    raise ValueError("database role artifact size does not match its manifest")

  runtime_contract_metadata = manifest.get("runtime_contract")
  if not isinstance(runtime_contract_metadata, dict):
    raise ValueError("database runtime contract artifact metadata is missing")
  runtime_contract_path = artifact_root / RUNTIME_CONTRACT_FILE_NAME
  if runtime_contract_metadata.get("path") != (
    f"/app/database-contract/{RUNTIME_CONTRACT_FILE_NAME}"
  ):
    raise ValueError("database runtime contract artifact path is invalid")
  if runtime_contract_metadata.get("sha256") != _artifact_digest(runtime_contract_path):
    raise ValueError("database runtime contract artifact digest does not match")
  if runtime_contract_metadata.get("size") != runtime_contract_path.stat().st_size:
    raise ValueError("database runtime contract artifact size does not match")

  runtime_contract = _read_json_object(runtime_contract_path)
  if runtime_contract.get("revision") != manifest["contract_revision"]:
    raise ValueError("embedded runtime and schema contract revisions differ")
  if runtime_contract.get("source_revision") != source_revision:
    raise ValueError("embedded runtime and schema source revisions differ")
  return manifest
