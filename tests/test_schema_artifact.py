"""Neutral database schema release evidence."""

import json
from pathlib import Path

import pytest

from app.database_contract.constants import CONTRACT_REVISION
from app.database_contract.schema_artifact import (
  MANIFEST_FILE_NAME,
  ROLES_FILE_NAME,
  RUNTIME_CONTRACT_FILE_NAME,
  SCHEMA_FILE_NAME,
  create_schema_manifest,
  read_schema_manifest,
)


SOURCE_REVISION = "a" * 40


def _write_contract(path: Path, source_revision: str = SOURCE_REVISION) -> None:
  path.write_text(
    json.dumps(
      {
        "revision": CONTRACT_REVISION,
        "source_revision": source_revision,
      }
    )
  )


def _write_artifact(artifact_root: Path) -> None:
  schema_path = artifact_root / SCHEMA_FILE_NAME
  roles_path = artifact_root / ROLES_FILE_NAME
  contract_path = artifact_root / RUNTIME_CONTRACT_FILE_NAME
  manifest_path = artifact_root / MANIFEST_FILE_NAME
  schema_path.write_text("CREATE SCHEMA inkcre;\n")
  roles_path.write_text("CREATE ROLE authenticated NOLOGIN;\n")
  _write_contract(contract_path)
  manifest = create_schema_manifest(
    schema_path,
    roles_path,
    contract_path,
    SOURCE_REVISION,
  )
  manifest_path.write_text(json.dumps(manifest))


def test_schema_manifest_binds_schema_contract_and_source(tmp_path):
  _write_artifact(tmp_path)

  manifest = read_schema_manifest(tmp_path)

  assert manifest["contract_revision"] == CONTRACT_REVISION
  assert manifest["source_revision"] == SOURCE_REVISION
  assert manifest["schema"]["size"] == len("CREATE SCHEMA inkcre;\n")


def test_schema_manifest_rejects_a_different_runtime_source(tmp_path):
  schema_path = tmp_path / SCHEMA_FILE_NAME
  roles_path = tmp_path / ROLES_FILE_NAME
  contract_path = tmp_path / RUNTIME_CONTRACT_FILE_NAME
  schema_path.write_text("CREATE SCHEMA inkcre;\n")
  roles_path.write_text("CREATE ROLE authenticated NOLOGIN;\n")
  _write_contract(contract_path, "b" * 40)

  with pytest.raises(ValueError, match="source revision does not match"):
    create_schema_manifest(schema_path, roles_path, contract_path, SOURCE_REVISION)


def test_schema_manifest_rejects_schema_tampering(tmp_path):
  _write_artifact(tmp_path)
  (tmp_path / SCHEMA_FILE_NAME).write_text("CREATE SCHEMA changed;\n")

  with pytest.raises(ValueError, match="digest does not match"):
    read_schema_manifest(tmp_path)


def test_schema_manifest_rejects_role_tampering(tmp_path):
  _write_artifact(tmp_path)
  (tmp_path / ROLES_FILE_NAME).write_text("CREATE ROLE unexpected;\n")

  with pytest.raises(ValueError, match="role artifact digest does not match"):
    read_schema_manifest(tmp_path)


def test_schema_manifest_rejects_runtime_contract_tampering(tmp_path):
  _write_artifact(tmp_path)
  contract_path = tmp_path / RUNTIME_CONTRACT_FILE_NAME
  runtime_contract = json.loads(contract_path.read_text())
  runtime_contract["commands"] = ["unexpected"]
  contract_path.write_text(json.dumps(runtime_contract))

  with pytest.raises(ValueError, match="runtime contract artifact digest does not match"):
    read_schema_manifest(tmp_path)
