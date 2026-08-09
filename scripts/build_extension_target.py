"""Build and bind a deterministic checked-in Python Extension target."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from typing import Any
import zipfile


FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
# Stored entries avoid zlib-version-dependent bytes. The bundle is small, and
# cross-run identity is more valuable than compression for an immutable target.
ZIP_COMPRESSION = zipfile.ZIP_STORED
ZIP_FILE_MODE = stat.S_IFREG | 0o644

EXCLUDED_DIRECTORY_NAMES = frozenset(
  {
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "cache",
    "dist",
  }
)
EXCLUDED_FILE_SUFFIXES = frozenset({".pyc", ".pyo"})

EXTENSION_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
TARGET_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
HEX_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")

CONFIG_KEYS = frozenset(
  {
    "schema_version",
    "coordinate",
    "version",
    "target_key",
    "artifact_format",
    "entrypoint",
    "conditions",
  }
)
MANIFEST_KEYS = frozenset(
  {"schema_version", "artifact_format", "entrypoint", "conditions", "files"}
)
CONDITION_KEYS = frozenset({"key", "operator", "value"})
FILE_DESCRIPTOR_KEYS = frozenset({"sha256", "size", "media_type"})


def _atomic_write(path: Path, content: bytes) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  descriptor, temporary_name = tempfile.mkstemp(
    dir=path.parent,
    prefix=f".{path.name}.",
    suffix=".tmp",
  )
  temporary_path = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "wb") as temporary:
      temporary.write(content)
      temporary.flush()
      os.fsync(temporary.fileno())
    temporary_path.chmod(0o644)
    temporary_path.replace(path)
  except BaseException:
    temporary_path.unlink(missing_ok=True)
    raise


def _is_excluded(relative_path: Path) -> bool:
  return (
    any(part in EXCLUDED_DIRECTORY_NAMES for part in relative_path.parts[:-1])
    or relative_path.suffix in EXCLUDED_FILE_SUFFIXES
  )


def _extension_files(project_root: Path, extension_id: str) -> list[tuple[str, bytes]]:
  if not EXTENSION_ID_PATTERN.fullmatch(extension_id):
    raise ValueError("extension id must be canonical snake_case")

  extension_namespace = project_root / "extensions"
  extension_root = extension_namespace / extension_id
  if not extension_root.is_dir():
    raise ValueError(f"extension source directory does not exist: {extension_root}")

  namespace_init = extension_namespace / "__init__.py"
  if namespace_init.is_symlink():
    raise ValueError(f"extension files must not be symbolic links: {namespace_init}")
  namespace_content = namespace_init.read_bytes() if namespace_init.is_file() else b""
  files = [("extensions/__init__.py", namespace_content)]

  for candidate in sorted(extension_root.rglob("*"), key=lambda path: path.as_posix()):
    relative_to_extension = candidate.relative_to(extension_root)
    if _is_excluded(relative_to_extension):
      continue
    if candidate.is_symlink():
      raise ValueError(f"extension files must not be symbolic links: {candidate}")
    if candidate.is_dir():
      continue
    if not candidate.is_file():
      raise ValueError(f"extension input must be a regular file: {candidate}")
    archive_path = candidate.relative_to(project_root).as_posix()
    files.append((archive_path, candidate.read_bytes()))

  return sorted(files, key=lambda item: item[0])


def build_python_bundle(
  project_root: Path,
  extension_id: str,
  output: Path,
) -> None:
  """Write one byte-reproducible ZIP containing an Extension package."""

  project_root = project_root.resolve()
  extension_root = (project_root / "extensions" / extension_id).resolve()
  output = output.resolve()
  if output.is_relative_to(extension_root):
    raise ValueError("bundle output must be outside the extension source directory")

  files = _extension_files(project_root, extension_id)
  output.parent.mkdir(parents=True, exist_ok=True)
  descriptor, temporary_name = tempfile.mkstemp(
    dir=output.parent,
    prefix=f".{output.name}.",
    suffix=".tmp",
  )
  os.close(descriptor)
  temporary_path = Path(temporary_name)
  try:
    with zipfile.ZipFile(
      temporary_path,
      mode="w",
      compression=ZIP_COMPRESSION,
      strict_timestamps=True,
    ) as archive:
      archive.comment = b""
      for archive_path, content in files:
        info = zipfile.ZipInfo(archive_path, date_time=FIXED_ZIP_TIMESTAMP)
        info.create_system = 3
        info.compress_type = ZIP_COMPRESSION
        info.external_attr = ZIP_FILE_MODE << 16
        info.extra = b""
        info.comment = b""
        archive.writestr(
          info,
          content,
          compress_type=ZIP_COMPRESSION,
        )
    temporary_path.chmod(0o644)
    temporary_path.replace(output)
  except BaseException:
    temporary_path.unlink(missing_ok=True)
    raise


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
  value: dict[str, Any] = {}
  for key, item in pairs:
    if key in value:
      raise ValueError(f"JSON object contains duplicate key: {key}")
    value[key] = item
  return value


def _read_json_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
  encoded = path.read_bytes()
  try:
    value = json.loads(
      encoded,
      object_pairs_hook=_object_without_duplicate_keys,
    )
  except (UnicodeDecodeError, json.JSONDecodeError) as error:
    raise ValueError(f"{label} must be valid UTF-8 JSON") from error
  if not isinstance(value, dict):
    raise ValueError(f"{label} must be a JSON object")
  return value, encoded


def _require_exact_keys(
  value: dict[str, Any], expected: frozenset[str], label: str
) -> None:
  actual = frozenset(value)
  if actual != expected:
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    raise ValueError(
      f"{label} keys do not match contract; missing={missing}, unexpected={unexpected}"
    )


def _validated_conditions(value: Any, label: str) -> list[dict[str, str]]:
  if not isinstance(value, list) or not value:
    raise ValueError(f"{label} conditions must be a non-empty array")

  conditions: list[dict[str, str]] = []
  condition_names: set[str] = set()
  for index, condition in enumerate(value):
    if not isinstance(condition, dict):
      raise ValueError(f"{label} condition {index} must be an object")
    _require_exact_keys(condition, CONDITION_KEYS, f"{label} condition {index}")
    if not all(isinstance(condition[key], str) for key in CONDITION_KEYS):
      raise ValueError(f"{label} condition {index} values must be strings")
    if condition["operator"] not in {"equals", "semver"}:
      raise ValueError(f"{label} condition {index} has an unsupported operator")
    if condition["key"] in condition_names:
      raise ValueError(f"{label} condition keys must be unique")
    condition_names.add(condition["key"])
    conditions.append(
      {
        "key": condition["key"],
        "operator": condition["operator"],
        "value": condition["value"],
      }
    )
  return conditions


def _condition_sort_key(condition: dict[str, str]) -> tuple[str, str, str]:
  return condition["key"], condition["operator"], condition["value"]


def _validate_config(config: dict[str, Any]) -> tuple[str, str, list[dict[str, str]]]:
  _require_exact_keys(config, CONFIG_KEYS, "target publish config")
  try:
    from inkcre_extension_registry.contracts.models import TargetPublishConfig
  except ImportError as error:
    raise RuntimeError(
      "catalog generation requires the pinned Extension Registry Runtime/API"
    ) from error

  try:
    validated = TargetPublishConfig.model_validate(config)
  except ValueError as error:
    raise ValueError(
      "target publish config does not satisfy the Registry contract"
    ) from error

  entrypoint = config["entrypoint"]
  if not isinstance(entrypoint, str) or not entrypoint:
    raise ValueError("target entrypoint must be a non-empty relative POSIX path")
  entrypoint_path = PurePosixPath(entrypoint)
  if (
    entrypoint_path.is_absolute()
    or not entrypoint_path.parts
    or len(entrypoint_path.parts) != 1
    or any(part in {"", ".", ".."} for part in entrypoint_path.parts)
    or entrypoint_path.as_posix() != entrypoint
  ):
    raise ValueError("target entrypoint must be one normalized root-level file name")

  conditions = _validated_conditions(config["conditions"], "target publish config")
  return validated.namespace, validated.name, conditions


def _validate_manifest(
  manifest: dict[str, Any],
  encoded: bytes,
  config: dict[str, Any],
  config_conditions: list[dict[str, str]],
  bundle: Path,
) -> bytes:
  _require_exact_keys(manifest, MANIFEST_KEYS, "target manifest")
  try:
    from inkcre_extension_registry.contracts.models import TargetManifest
  except ImportError as error:
    raise RuntimeError(
      "catalog generation requires the pinned Extension Registry Runtime/API"
    ) from error
  try:
    validated = TargetManifest.model_validate(manifest)
  except ValueError as error:
    raise ValueError("target manifest does not satisfy the Registry contract") from error

  if manifest["artifact_format"] != config["artifact_format"]:
    raise ValueError("target manifest artifact format does not match config")
  if manifest["entrypoint"] != config["entrypoint"]:
    raise ValueError("target manifest entrypoint does not match config")

  manifest_conditions = _validated_conditions(manifest["conditions"], "target manifest")
  if sorted(manifest_conditions, key=_condition_sort_key) != sorted(
    config_conditions,
    key=_condition_sort_key,
  ):
    raise ValueError("target manifest conditions do not match config")

  files = manifest["files"]
  if not isinstance(files, dict) or set(files) != {config["entrypoint"]}:
    raise ValueError("target manifest must declare only its bundle entrypoint")
  descriptor = files[config["entrypoint"]]
  if not isinstance(descriptor, dict):
    raise ValueError("target bundle descriptor must be an object")
  _require_exact_keys(descriptor, FILE_DESCRIPTOR_KEYS, "target bundle descriptor")
  if not isinstance(descriptor["sha256"], str) or not HEX_DIGEST_PATTERN.fullmatch(
    descriptor["sha256"]
  ):
    raise ValueError("target bundle descriptor digest is invalid")
  if type(descriptor["size"]) is not int or descriptor["size"] < 0:
    raise ValueError("target bundle descriptor size is invalid")
  if descriptor["media_type"] != "application/zip":
    raise ValueError("target bundle descriptor media type must be application/zip")

  canonical = validated.canonical_bytes()
  if encoded != canonical + b"\n":
    raise ValueError("target manifest is not canonical Registry output")

  bundle_content = bundle.read_bytes()
  bundle_digest = hashlib.sha256(bundle_content).hexdigest()
  if descriptor["sha256"] != bundle_digest:
    raise ValueError("target bundle digest does not match manifest")
  if descriptor["size"] != len(bundle_content):
    raise ValueError("target bundle size does not match manifest")
  return canonical


def write_target_catalog(  # noqa: PLR0913 - paths make each trust input explicit
  config_path: Path,
  extension_id: str,
  bundle_path: Path,
  manifest_path: Path,
  output: Path,
  container_root: PurePosixPath = PurePosixPath("/app/extension-targets"),
) -> dict[str, Any]:
  """Validate CLI output against local bytes and write the admission catalog."""

  if not EXTENSION_ID_PATTERN.fullmatch(extension_id):
    raise ValueError("extension id must be canonical snake_case")
  if not container_root.is_absolute() or ".." in container_root.parts:
    raise ValueError("container root must be an absolute normalized POSIX path")

  config, _ = _read_json_object(config_path, "target publish config")
  namespace, name, config_conditions = _validate_config(config)
  if name != extension_id:
    raise ValueError("extension id must match the Registry target name")
  if bundle_path.name != config["entrypoint"]:
    raise ValueError("bundle file name must match the configured entrypoint")

  manifest, manifest_encoded = _read_json_object(manifest_path, "target manifest")
  canonical_manifest = _validate_manifest(
    manifest,
    manifest_encoded,
    config,
    config_conditions,
    bundle_path,
  )
  target_digest = f"sha256:{hashlib.sha256(canonical_manifest).hexdigest()}"
  if not TARGET_DIGEST_PATTERN.fullmatch(target_digest):
    raise AssertionError("computed target digest is not canonical")

  target_root = container_root / extension_id
  catalog = {
    "schema_version": 1,
    "targets": [
      {
        "namespace": namespace,
        "name": name,
        "version": config["version"],
        "target_key": config["target_key"],
        "target_digest": target_digest,
        "extension_id": extension_id,
        "bundle_path": str(target_root / config["entrypoint"]),
        "manifest_path": str(target_root / "manifest.json"),
      }
    ],
  }
  _atomic_write(
    output,
    (json.dumps(catalog, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
  )
  return catalog


def _build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    description="Build one deterministic checked-in Python Extension target."
  )
  subparsers = parser.add_subparsers(dest="command", required=True)

  bundle = subparsers.add_parser("bundle", help="build the deterministic Python ZIP")
  bundle.add_argument("--project-root", type=Path, default=Path("."))
  bundle.add_argument("--extension-id", required=True)
  bundle.add_argument("--output", type=Path, required=True)

  catalog = subparsers.add_parser(
    "catalog",
    help="validate a canonical target manifest and write the admission catalog",
  )
  catalog.add_argument("--config", type=Path, required=True)
  catalog.add_argument("--extension-id", required=True)
  catalog.add_argument("--bundle", type=Path, required=True)
  catalog.add_argument("--manifest", type=Path, required=True)
  catalog.add_argument("--output", type=Path, required=True)
  catalog.add_argument(
    "--container-root",
    type=PurePosixPath,
    default=PurePosixPath("/app/extension-targets"),
  )
  return parser


def main() -> None:
  args = _build_parser().parse_args()
  if args.command == "bundle":
    build_python_bundle(args.project_root, args.extension_id, args.output)
    return
  if args.command == "catalog":
    catalog = write_target_catalog(
      args.config,
      args.extension_id,
      args.bundle,
      args.manifest,
      args.output,
      args.container_root,
    )
    print(catalog["targets"][0]["target_digest"])
    return
  raise AssertionError(f"unsupported command: {args.command}")


if __name__ == "__main__":
  main()
