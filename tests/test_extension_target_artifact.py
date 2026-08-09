"""Deterministic Python target and local admission catalog contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import zipfile

import pytest

from inkcre_extension_registry.contracts.models import TargetManifest
from scripts.build_extension_target import (
  FIXED_ZIP_TIMESTAMP,
  ZIP_COMPRESSION,
  build_python_bundle,
  write_target_catalog,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGET_CONFIG_PATH = PROJECT_ROOT / "extensions/twitter/target-publish.json"
CATALOG_SCHEMA_PATH = PROJECT_ROOT / "contracts/extension-target-catalog.schema.json"
CATALOG_FIXTURE_PATH = PROJECT_ROOT / "tests/fixtures/extension-target-catalog.json"

TARGET_CONFIG = {
  "schema_version": 1,
  "coordinate": "inkcre/twitter",
  "version": "0.1.0",
  "target_key": "python-core-v1",
  "artifact_format": "python-bundle-v1",
  "entrypoint": "bundle.zip",
  "conditions": [
    {
      "key": "inkcre.integration",
      "operator": "equals",
      "value": "python-bundle-v1",
    },
    {
      "key": "inkcre.extension-api",
      "operator": "semver",
      "value": "^1.0.0",
    },
    {
      "key": "python",
      "operator": "semver",
      "value": ">=3.12.0 <3.13.0",
    },
  ],
}


def _copy_extension_project(destination: Path) -> Path:
  extension_namespace = destination / "extensions"
  extension_namespace.mkdir(parents=True)
  shutil.copytree(
    PROJECT_ROOT / "extensions/twitter",
    extension_namespace / "twitter",
    ignore=shutil.ignore_patterns(
      ".cache",
      ".mypy_cache",
      ".pytest_cache",
      ".ruff_cache",
      "__pycache__",
      "*.pyc",
      "*.pyo",
    ),
  )
  return destination


def _write_registry_manifest(bundle_path: Path, manifest_path: Path) -> TargetManifest:
  config = json.loads(TARGET_CONFIG_PATH.read_text(encoding="utf-8"))
  bundle = bundle_path.read_bytes()
  manifest = TargetManifest(
    artifact_format=config["artifact_format"],
    entrypoint=config["entrypoint"],
    conditions=config["conditions"],
    files={
      "bundle.zip": {
        "sha256": hashlib.sha256(bundle).hexdigest(),
        "size": len(bundle),
        "media_type": "application/zip",
      }
    },
  )
  manifest_path.write_bytes(manifest.canonical_bytes() + b"\n")
  return manifest


def test_twitter_target_publish_config_is_exact() -> None:
  assert json.loads(TARGET_CONFIG_PATH.read_text(encoding="utf-8")) == TARGET_CONFIG


def test_bundle_is_byte_reproducible_and_has_fixed_metadata(tmp_path: Path) -> None:
  project_root = _copy_extension_project(tmp_path / "project")
  extension_root = project_root / "extensions/twitter"
  (extension_root / "__pycache__").mkdir()
  (extension_root / "__pycache__/ignored.pyc").write_bytes(b"cache")
  (extension_root / "cache").mkdir()
  (extension_root / "cache/ignored.py").write_text("ignored = True\n")
  (extension_root / "dist").mkdir()
  (extension_root / "dist/ignored.py").write_text("ignored = True\n")

  first = tmp_path / "first/bundle.zip"
  second = tmp_path / "second/bundle.zip"
  separate_process = tmp_path / "separate-process/bundle.zip"
  build_python_bundle(project_root, "twitter", first)
  build_python_bundle(project_root, "twitter", second)
  subprocess.run(  # noqa: S603 - fixed interpreter and repository-owned script
    [
      sys.executable,
      str(PROJECT_ROOT / "scripts/build_extension_target.py"),
      "bundle",
      "--project-root",
      str(project_root),
      "--extension-id",
      "twitter",
      "--output",
      str(separate_process),
    ],
    check=True,
  )

  assert first.read_bytes() == second.read_bytes()
  assert first.read_bytes() == separate_process.read_bytes()
  with zipfile.ZipFile(first) as archive:
    names = archive.namelist()
    assert names == sorted(names)
    assert "extensions/__init__.py" in names
    assert "extensions/twitter/__init__.py" in names
    assert "extensions/twitter/target-publish.json" in names
    assert not any("cache" in Path(name).parts for name in names)
    assert not any("dist" in Path(name).parts for name in names)
    assert not any(name.endswith((".pyc", ".pyo")) for name in names)
    assert archive.read("extensions/__init__.py") == b""
    assert archive.comment == b""
    for info in archive.infolist():
      mode = info.external_attr >> 16
      assert info.date_time == FIXED_ZIP_TIMESTAMP
      assert info.create_system == 3
      assert stat.S_IFMT(mode) == stat.S_IFREG
      assert stat.S_IMODE(mode) == 0o644
      assert info.compress_type == ZIP_COMPRESSION
      assert info.extra == b""
      assert info.comment == b""


def test_bundle_is_the_import_authority_for_twitter(tmp_path: Path) -> None:
  project_root = _copy_extension_project(tmp_path / "project")
  bundle = tmp_path / "bundle.zip"
  build_python_bundle(project_root, "twitter", bundle)

  probe = subprocess.run(  # noqa: S603 - fixed interpreter probes isolated zipimport
    [
      sys.executable,
      "-I",
      "-c",
      (
        "import importlib.util, sys; "
        "sys.path.insert(0, sys.argv[1]); "
        "spec = importlib.util.find_spec('extensions.twitter'); "
        "assert spec is not None and spec.origin is not None; "
        "print(spec.origin)"
      ),
      str(bundle),
    ],
    cwd=tmp_path,
    check=True,
    capture_output=True,
    text=True,
  )

  assert probe.stdout.strip() == f"{bundle}/extensions/twitter/__init__.py"


def test_catalog_binds_registry_manifest_to_exact_bundle(tmp_path: Path) -> None:
  project_root = _copy_extension_project(tmp_path / "project")
  target_root = tmp_path / "release/extension-targets/twitter"
  bundle_path = target_root / "bundle.zip"
  manifest_path = target_root / "manifest.json"
  catalog_path = target_root.parent / "catalog.json"
  build_python_bundle(project_root, "twitter", bundle_path)
  manifest = _write_registry_manifest(bundle_path, manifest_path)

  catalog = write_target_catalog(
    TARGET_CONFIG_PATH,
    "twitter",
    bundle_path,
    manifest_path,
    catalog_path,
  )

  assert json.loads(catalog_path.read_text(encoding="utf-8")) == catalog
  assert catalog["schema_version"] == 1
  target = catalog["targets"][0]
  assert target["target_digest"] == manifest.digest
  assert target["bundle_path"] == "/app/extension-targets/twitter/bundle.zip"
  assert target["manifest_path"] == "/app/extension-targets/twitter/manifest.json"

  fixture_target = json.loads(CATALOG_FIXTURE_PATH.read_text(encoding="utf-8"))["targets"][
    0
  ]
  fixture_target["target_digest"] = manifest.digest
  assert target == fixture_target


def test_catalog_rejects_bundle_tampering(tmp_path: Path) -> None:
  project_root = _copy_extension_project(tmp_path / "project")
  bundle_path = tmp_path / "bundle.zip"
  manifest_path = tmp_path / "manifest.json"
  build_python_bundle(project_root, "twitter", bundle_path)
  _write_registry_manifest(bundle_path, manifest_path)
  bundle_path.write_bytes(bundle_path.read_bytes() + b"tampered")

  with pytest.raises(ValueError, match="bundle digest does not match"):
    write_target_catalog(
      TARGET_CONFIG_PATH,
      "twitter",
      bundle_path,
      manifest_path,
      tmp_path / "catalog.json",
    )


def test_catalog_rejects_noncanonical_manifest_tampering(tmp_path: Path) -> None:
  project_root = _copy_extension_project(tmp_path / "project")
  bundle_path = tmp_path / "bundle.zip"
  manifest_path = tmp_path / "manifest.json"
  build_python_bundle(project_root, "twitter", bundle_path)
  _write_registry_manifest(bundle_path, manifest_path)
  manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

  with pytest.raises(ValueError, match="not canonical Registry output"):
    write_target_catalog(
      TARGET_CONFIG_PATH,
      "twitter",
      bundle_path,
      manifest_path,
      tmp_path / "catalog.json",
    )


@pytest.mark.parametrize("version", ["1.0", "v1.0.0", "1.0.0+local"])
def test_catalog_rejects_noncanonical_registry_version(
  tmp_path: Path,
  version: str,
) -> None:
  config = dict(TARGET_CONFIG)
  config["version"] = version
  config_path = tmp_path / "target-publish.json"
  config_path.write_text(json.dumps(config), encoding="utf-8")

  with pytest.raises(ValueError, match="does not satisfy the Registry contract"):
    write_target_catalog(
      config_path,
      "twitter",
      tmp_path / "bundle.zip",
      tmp_path / "manifest.json",
      tmp_path / "catalog.json",
    )


@pytest.mark.parametrize(
  "entrypoint",
  [
    "",
    ".",
    "../bundle.zip",
    "./bundle.zip",
    "/bundle.zip",
    "files/../bundle.zip",
    "files/bundle.zip",
  ],
)
def test_catalog_rejects_unsafe_or_noncanonical_entrypoint(
  tmp_path: Path,
  entrypoint: str,
) -> None:
  config = dict(TARGET_CONFIG)
  config["entrypoint"] = entrypoint
  config_path = tmp_path / "target-publish.json"
  config_path.write_text(json.dumps(config), encoding="utf-8")

  with pytest.raises(ValueError, match="entrypoint|Registry contract"):
    write_target_catalog(
      config_path,
      "twitter",
      tmp_path / "bundle.zip",
      tmp_path / "manifest.json",
      tmp_path / "catalog.json",
    )


def test_catalog_schema_and_fixture_define_the_exact_surface() -> None:
  schema = json.loads(CATALOG_SCHEMA_PATH.read_text(encoding="utf-8"))
  fixture = json.loads(CATALOG_FIXTURE_PATH.read_text(encoding="utf-8"))
  target_schema = schema["properties"]["targets"]["items"]

  assert schema["properties"]["schema_version"] == {"const": 1}
  assert schema["additionalProperties"] is False
  assert target_schema["additionalProperties"] is False
  assert set(target_schema["required"]) == set(fixture["targets"][0])
  version_pattern = re.compile(target_schema["properties"]["version"]["pattern"])
  assert version_pattern.fullmatch("0.1.0")
  assert version_pattern.fullmatch("1.0.0-alpha.1")
  assert not version_pattern.fullmatch("1.0")
  assert not version_pattern.fullmatch("1.0.0-01")
  assert not version_pattern.fullmatch("1.0.0+build")
