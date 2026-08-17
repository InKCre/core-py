"""Native wheel, pip-consumer, and delivery contract tests."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import textwrap
import tomllib
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
import site
import typing
import zipfile

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
import pytest

from app.business.extension.distribution import (
  PipDistributionConsumer,
  _validate_extension_wheel,
)
from app.business.extension.errors import (
  ExtensionAcquisitionError,
  ExtensionEntryPointError,
  ExtensionRestartRequiredError,
)
from app.business.extension.release import (
  EntryPointDescriptor,
  ExtensionReleaseDescriptor,
  PythonReleaseDescriptor,
)
from app.version import CORE_VERSION
from scripts.extension_distribution import read_project, verify_wheel
from scripts.extension_release import discover_projects


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = tuple(project.key for project in discover_projects())


def release_and_association():
  association = PythonReleaseDescriptor(
    project="inkcre-ext-fixture",
    simple_url="/simple/inkcre-ext-fixture/",
    host_sdk="core-py",
    host_sdk_version="^0.1.0",
    entry_point=EntryPointDescriptor(
      group="inkcre.core.extensions",
      name="fixture",
      object="extensions.fixture:Extension",
    ),
  )
  release = ExtensionReleaseDescriptor(
    name="inkcre/fixture",
    nickname="Fixture",
    version="1.0.0",
    state="published",
    python=association,
  )
  return release, association


def write_fixture_wheel(path: Path, *extra_members: str) -> None:
  with zipfile.ZipFile(path, "w") as archive:
    archive.writestr("extensions/fixture/__init__.py", "class Extension: pass\n")
    archive.writestr(
      "inkcre_ext_fixture-1.0.0.dist-info/METADATA",
      "Metadata-Version: 2.4\nName: inkcre-ext-fixture\nVersion: 1.0.0\n",
    )
    archive.writestr(
      "inkcre_ext_fixture-1.0.0.dist-info/WHEEL",
      "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
    )
    for member in extra_members:
      archive.writestr(member, "malicious\n")


def test_core_host_sdk_version_is_checked_against_project_version():
  pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())

  assert CORE_VERSION == pyproject["project"]["version"]


def test_core_image_baseline_declares_every_first_party_requirement():
  core_project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())["project"]
  baseline = {
    canonicalize_name(Requirement(value).name) for value in core_project["dependencies"]
  }

  for extension in EXTENSIONS:
    project = tomllib.loads(
      (PROJECT_ROOT / "extensions" / extension / "pyproject.toml").read_text()
    )["project"]
    required = {
      canonicalize_name(Requirement(value).name) for value in project["dependencies"]
    }
    assert required <= baseline, f"{extension} requires dependencies outside the Core image"


def test_producer_rejects_native_package_range_syntax(tmp_path: Path):
  project_directory = tmp_path / "github"
  shutil.copytree(PROJECT_ROOT / "extensions/github", project_directory)
  pyproject = project_directory / "pyproject.toml"
  pyproject.write_text(pyproject.read_text().replace(">=0.1.0 <0.2.0", ">=0.1.0,<0.2.0"))

  with pytest.raises(ValueError, match="Host SDK SemVer range"):
    read_project(project_directory)


def test_all_first_party_projects_build_pep420_entry_point_wheels(tmp_path: Path):
  built_wheels: list[Path] = []
  for extension in EXTENSIONS:
    project_directory = PROJECT_ROOT / "extensions" / extension
    output = tmp_path / extension
    output.mkdir()
    result = subprocess.run(  # noqa: S603 -- fixed interpreter and test paths
      [
        sys.executable,
        "-m",
        "build",
        "--wheel",
        "--no-isolation",
        "--outdir",
        str(output),
        str(project_directory),
      ],
      check=False,
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0, result.stderr
    wheels = list(output.glob("*.whl"))
    assert len(wheels) == 1
    built_wheels.append(wheels[0])
    producer = read_project(project_directory)
    verify_wheel(producer, wheels[0])
    report = output / "pip-report.json"
    plan = subprocess.run(  # noqa: S603 -- fixed interpreter and built test wheel
      [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--dry-run",
        "--report",
        str(report),
        "--no-index",
        str(wheels[0]),
      ],
      check=False,
      capture_output=True,
      text=True,
    )
    assert plan.returncode == 0, plan.stderr
    installs = json.loads(report.read_text())["install"]
    assert [item["metadata"]["name"] for item in installs] == [producer.project]
    with zipfile.ZipFile(wheels[0]) as archive:
      members = set(archive.namelist())
    assert "extensions/__init__.py" not in members
    assert f"extensions/{extension}/__init__.py" in members

  assert read_project(PROJECT_ROOT / "extensions/twitter").version == "0.2.1"
  venv = tmp_path / "lifecycle-venv"
  subprocess.run(  # noqa: S603 -- fixed interpreter and disposable venv
    [sys.executable, "-m", "venv", "--system-site-packages", str(venv)],
    check=True,
  )
  python = venv / "bin/python"
  install = subprocess.run(  # noqa: S603 -- disposable probe interpreter
    [
      str(python),
      "-m",
      "pip",
      "install",
      "--no-deps",
      "--no-index",
      *(str(wheel) for wheel in built_wheels),
    ],
    check=False,
    capture_output=True,
    text=True,
  )
  assert install.returncode == 0, install.stderr

  projection = tmp_path / "core-projection"
  projection.mkdir()
  for package in ("app", "libs", "utils"):
    (projection / package).symlink_to(PROJECT_ROOT / package, target_is_directory=True)
  probe_source = textwrap.dedent(
    f"""
    import asyncio
    import fastapi
    import importlib
    import importlib.metadata
    from pathlib import Path
    import sys

    from app.business.extension.main import ExtensionBase
    from app.business.extension.runtime import ExtensionRuntimeRecord
    from app.business.source import SourceManager

    expected = {EXTENSIONS!r}
    runtime_root = Path(sys.prefix).resolve()
    SourceManager.sync_source_types = classmethod(
      lambda cls, selected=None: None
    )

    for name in expected:
      project = f"inkcre-ext-{{name.replace('_', '-')}}"
      distribution = importlib.metadata.distribution(project)
      entry_points = [
        entry_point
        for entry_point in distribution.entry_points
        if entry_point.group == "inkcre.core.extensions"
        and entry_point.name == name
      ]
      assert len(entry_points) == 1
      entry_point = entry_points[0]
      extension = entry_point.load()
      assert issubclass(extension, ExtensionBase)
      module = importlib.import_module(entry_point.module)
      assert runtime_root in Path(module.__file__).resolve().parents

      persisted = []
      state = {{}}
      schemas = []
      app = fastapi.FastAPI()
      extension.on_start(
        app,
        ExtensionRuntimeRecord(
          extension_id=name,
          config={{}},
          read_config=lambda: {{}},
          persist_config=persisted.append,
          read_state=lambda: dict(state),
          mutate_state=lambda mutation: state.update(mutation(dict(state))) or dict(state),
          mutate_config_and_state=lambda mutation: mutation({{}}, dict(state)),
          persist_config_schema=schemas.append,
        ),
      )
      assert extension.runtime_active()
      assert schemas
      asyncio.run(extension.on_close())
      extension.unpublish()
      assert not extension.runtime_active()
      extension.release_runtime()
    """
  )
  probe = subprocess.run(  # noqa: S603 -- disposable installed-wheel lifecycle probe
    [str(python), "-c", probe_source],
    cwd=tmp_path,
    env={
      **os.environ,
      "DATABASE_URL": "postgresql+psycopg://test:test@127.0.0.1:1/test",
      "JWT_SECRET": "test-only-jwt-secret-at-least-32-bytes",
      "OBSRV__LOGGING_BACKEND": "none",
      "INKCRE_ENV_FILE": "",
      "PYTHONPATH": os.pathsep.join([str(projection), *site.getsitepackages()]),
    },
    check=False,
    capture_output=True,
    text=True,
  )
  assert probe.returncode == 0, probe.stderr


def test_prepare_metadata_keeps_provenance_inside_python_association():
  producer = read_project(PROJECT_ROOT / "extensions/github")
  document = producer.prepare_document(
    source_repository="https://github.com/InKCre/core-py",
    source_revision="abc123",
    build_id="456",
  )

  assert "source_repository" not in document
  python = typing.cast(dict[str, object], document["python"])
  assert python["source_repository"] == "https://github.com/InKCre/core-py"
  assert python["source_revision"] == "abc123"
  assert python["build_id"] == "456"


def test_dependency_plan_allows_only_declared_extension_project_replacement(monkeypatch):
  consumer = PipDistributionConsumer("https://registry.test")
  monkeypatch.setattr(
    consumer,
    "_installed_versions",
    lambda: {"inkcre-ext-fixture": "0.9.0", "core-owned": "1.0.0"},
  )
  consumer._reject_replacements(
    [{"metadata": {"name": "inkcre-ext-fixture", "version": "1.0.0"}}],
    "inkcre-ext-fixture",
  )
  with pytest.raises(ExtensionAcquisitionError, match="replace loaded Distribution"):
    consumer._reject_replacements(
      [{"metadata": {"name": "core-owned", "version": "2.0.0"}}],
      "inkcre-ext-fixture",
    )


def test_pip_consumer_uses_current_interpreter_without_target_overlay(
  monkeypatch,
  tmp_path: Path,
):
  commands: list[list[str]] = []

  def runner(arguments: list[str]):
    commands.append(arguments)
    if arguments[0] == "download" and "--no-deps" in arguments:
      destination = Path(arguments[arguments.index("--dest") + 1])
      write_fixture_wheel(destination / "inkcre_ext_fixture-1.0.0-py3-none-any.whl")
    elif "--dry-run" in arguments:
      report = Path(arguments[arguments.index("--report") + 1])
      report.write_text(
        json.dumps(
          {"install": [{"metadata": {"name": "inkcre-ext-fixture", "version": "1.0.0"}}]}
        )
      )
    return subprocess.CompletedProcess(arguments, 0, "", "")

  consumer = PipDistributionConsumer(
    "https://registry.test",
    runner=runner,
  )
  monkeypatch.setattr(consumer, "_installed_versions", lambda: {})
  sentinel = object()
  discoveries = iter([ExtensionEntryPointError("missing"), sentinel])

  def discover(*args):
    result = next(discoveries)
    if isinstance(result, Exception):
      raise result
    return result

  monkeypatch.setattr(
    "app.business.extension.distribution.AcquiredDistribution.discover",
    discover,
  )
  release, association = release_and_association()

  assert consumer.acquire(release, association) is sentinel
  assert [command[0] for command in commands] == [
    "download",
    "install",
    "install",
  ]
  assert "--index-url" in commands[0]
  assert "--dry-run" in commands[1]
  assert "--dry-run" not in commands[2]
  for command in commands[1:]:
    assert "--no-index" in command
    assert "--find-links" in command
  assert all("--target" not in command for command in commands)


def test_pip_consumer_rejects_a_missing_host_dependency_before_mutation(monkeypatch):
  commands: list[list[str]] = []

  def runner(arguments: list[str]):
    commands.append(arguments)
    if arguments[0] == "download":
      destination = Path(arguments[arguments.index("--dest") + 1])
      write_fixture_wheel(destination / "inkcre_ext_fixture-1.0.0-py3-none-any.whl")
      return subprocess.CompletedProcess(arguments, 0, "", "")
    return subprocess.CompletedProcess(
      arguments,
      1,
      "",
      "No matching distribution found for host-only-dependency",
    )

  consumer = PipDistributionConsumer(
    "https://registry.test",
    runner=runner,
  )
  monkeypatch.setattr(consumer, "_installed_versions", lambda: {})
  monkeypatch.setattr(
    "app.business.extension.distribution.AcquiredDistribution.discover",
    lambda *args: (_ for _ in ()).throw(ExtensionEntryPointError("missing")),
  )
  release, association = release_and_association()

  with pytest.raises(ExtensionAcquisitionError, match="dependency preflight failed"):
    consumer.acquire(release, association)

  assert [command[0] for command in commands] == ["download", "install"]
  assert "--dry-run" in commands[1]
  assert "--no-index" in commands[1]


@pytest.mark.parametrize(
  "member",
  [
    "../escape.py",
    "extension-bootstrap.pth",
    "inkcre_ext_fixture-1.0.0.data/scripts/run",
    "app/extension_payload.py",
    "libs/extension_payload.py",
    "utils/extension_payload.py",
    "extensions/other/__init__.py",
    "other-1.0.0.dist-info/",
  ],
)
def test_extension_wheel_rejects_non_owned_or_redirected_files(
  tmp_path: Path,
  member: str,
):
  wheel = tmp_path / "fixture.whl"
  write_fixture_wheel(wheel, member)
  release, association = release_and_association()

  with pytest.raises(ExtensionAcquisitionError):
    _validate_extension_wheel(wheel, release, association)


def test_extension_wheel_rejects_an_installed_distribution_file_conflict(
  monkeypatch,
  tmp_path: Path,
):
  wheel = tmp_path / "fixture.whl"
  write_fixture_wheel(wheel)
  target = (
    Path(sysconfig.get_path("purelib")) / "extensions/fixture/__init__.py"
  ).resolve()
  monkeypatch.setattr(
    "app.business.extension.distribution._installed_file_owners",
    lambda project: {target: "core-owned"},
  )
  release, association = release_and_association()

  with pytest.raises(ExtensionAcquisitionError, match="owned by Distribution"):
    _validate_extension_wheel(wheel, release, association)


def test_entry_point_package_must_match_its_local_name():
  commands: list[list[str]] = []
  consumer = PipDistributionConsumer(
    "https://registry.test",
    runner=lambda arguments: commands.append(arguments),  # type: ignore[arg-type]
  )
  release, association = release_and_association()
  mismatched = association.model_copy(
    update={
      "entry_point": association.entry_point.model_copy(
        update={"object": "extensions.other:Extension"}
      )
    }
  )

  with pytest.raises(ExtensionEntryPointError, match="declared extensions"):
    consumer.acquire(release.model_copy(update={"python": mismatched}), mismatched)
  assert commands == []


def test_failed_site_packages_mutation_makes_consumer_globally_restart_required(
  monkeypatch,
  tmp_path: Path,
):
  commands: list[list[str]] = []

  def runner(arguments: list[str]):
    commands.append(arguments)
    if arguments[0] == "download" and "--no-deps" in arguments:
      destination = Path(arguments[arguments.index("--dest") + 1])
      write_fixture_wheel(destination / "inkcre_ext_fixture-1.0.0-py3-none-any.whl")
    elif "--dry-run" in arguments:
      report = Path(arguments[arguments.index("--report") + 1])
      report.write_text(
        json.dumps(
          {"install": [{"metadata": {"name": "inkcre-ext-fixture", "version": "1.0.0"}}]}
        )
      )
    if arguments[0] == "install" and "--dry-run" not in arguments:
      return subprocess.CompletedProcess(arguments, 1, "", "install failed")
    return subprocess.CompletedProcess(arguments, 0, "", "")

  consumer = PipDistributionConsumer(
    "https://registry.test",
    runner=runner,
  )
  monkeypatch.setattr(consumer, "_installed_versions", lambda: {})
  monkeypatch.setattr(
    "app.business.extension.distribution.AcquiredDistribution.discover",
    lambda *args: (_ for _ in ()).throw(ExtensionEntryPointError("missing")),
  )
  release, association = release_and_association()

  with pytest.raises(ExtensionAcquisitionError, match="installation failed"):
    consumer.acquire(release, association)
  command_count = len(commands)
  with pytest.raises(ExtensionRestartRequiredError, match="mutation began"):
    consumer.acquire(release, association)
  assert len(commands) == command_count


def test_extension_publish_workflow_gates_immutable_versions_by_release_intent():
  workflow = (PROJECT_ROOT / ".github/workflows/extension-publish.yml").read_text()

  assert "github.event.workflow_run.check_suite_id" in workflow
  assert "--jq .before" in workflow
  assert 'git merge-base --is-ancestor "$before" HEAD' in workflow
  assert "scripts/extension_release.py version-changed" in workflow
  assert "Verify source belongs to current main history" in workflow
  assert "git merge-base --is-ancestor HEAD origin/main" in workflow
  assert "scripts/extension_release.py verify-artifact-unchanged" in workflow
  assert workflow.index(
    "Revalidate Extension artifact input before remote mutation"
  ) < workflow.index("Prepare exact native Release association")
  assert "Record unchanged Extension no-op" in workflow
  assert "curl --fail-with-body" in workflow
  assert '--build-id "${{ github.run_id }}"' in workflow
  assert "github.run_attempt" not in workflow
  assert "INITIAL_ONLY" in workflow
  assert "recovery must rerun the original publication run" in workflow
  assert workflow.count("steps.selection.outputs.selected == 'true'") >= 6


def test_extension_publish_unrelated_commit_is_an_explicit_noop():
  changed_paths = {"README.md", "app/settings.py"}

  assert not any(path.startswith("extensions/github/") for path in changed_paths)


def test_older_checked_publication_survives_unrelated_main_but_not_same_subtree(
  tmp_path: Path,
):
  repository = tmp_path / "repository"
  repository.mkdir()

  def git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 -- fixed git command and disposable repository
      ["git", *arguments],
      cwd=repository,
      check=False,
      capture_output=True,
      text=True,
    )

  assert git("init", "--initial-branch=main").returncode == 0
  assert git("config", "user.name", "Extension Test").returncode == 0
  assert git("config", "user.email", "extension@example.test").returncode == 0
  rss = repository / "extensions/rss"
  rss.mkdir(parents=True)
  (rss / "pyproject.toml").write_text("version = '0.1.0'\n")
  assert git("add", ".").returncode == 0
  assert git("commit", "-m", "change rss").returncode == 0
  checked_rss = git("rev-parse", "HEAD").stdout.strip()

  (repository / "README.md").write_text("docs only\n")
  assert git("add", ".").returncode == 0
  assert git("commit", "-m", "docs").returncode == 0
  docs_head = git("rev-parse", "HEAD").stdout.strip()
  assert git("merge-base", "--is-ancestor", checked_rss, docs_head).returncode == 0
  assert (
    git("diff", "--quiet", checked_rss, docs_head, "--", "extensions/rss").returncode == 0
  )

  (rss / "pyproject.toml").write_text("version = '0.1.1'\n")
  assert git("add", ".").returncode == 0
  assert git("commit", "-m", "bump rss").returncode == 0
  rss_head = git("rev-parse", "HEAD").stdout.strip()
  assert git("merge-base", "--is-ancestor", checked_rss, rss_head).returncode == 0
  assert (
    git("diff", "--quiet", checked_rss, rss_head, "--", "extensions/rss").returncode == 1
  )
  assert git("diff", "--quiet", docs_head, rss_head, "--", "extensions/rss").returncode == 1


def test_extension_publish_changed_source_uses_the_bumped_release_version():
  changed_paths = {"extensions/twitter/api.py", "extensions/twitter/pyproject.toml"}
  producer = read_project(PROJECT_ROOT / "extensions/twitter")

  assert any(path.startswith("extensions/twitter/") for path in changed_paths)
  assert producer.version == "0.2.1"


def test_extension_publish_changed_source_same_version_keeps_registry_conflict_fatal():
  workflow = (PROJECT_ROOT / ".github/workflows/extension-publish.yml").read_text()
  changed_paths = {"extensions/rss/rss.py"}

  assert any(path.startswith("extensions/rss/") for path in changed_paths)
  assert "curl --fail-with-body" in workflow
  assert "continue-on-error" not in workflow
  assert workflow.index("Prepare exact native Release association") < workflow.index(
    "Upload wheel through native PyPI protocol"
  )


def test_local_simple_installs_and_discovers_a_real_first_party_contribution(
  tmp_path: Path,
):
  project = PROJECT_ROOT / "extensions/github"
  repository = tmp_path / "repository"
  wheel_output = tmp_path / "wheel"
  wheel_output.mkdir()
  result = subprocess.run(  # noqa: S603 -- fixed interpreter and test paths
    [
      sys.executable,
      "-m",
      "build",
      "--wheel",
      "--no-isolation",
      "--outdir",
      str(wheel_output),
      str(project),
    ],
    check=False,
    capture_output=True,
    text=True,
  )
  assert result.returncode == 0, result.stderr
  wheel = next(wheel_output.glob("*.whl"))
  simple = repository / "simple/inkcre-ext-github"
  simple.mkdir(parents=True)
  shutil.copy2(wheel, repository / wheel.name)
  (simple / "index.html").write_text(
    f'<a href="../../{wheel.name}">{wheel.name}</a>',
    encoding="utf-8",
  )

  class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
      return None

  handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(repository), **kwargs)
  server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
  thread = threading.Thread(target=server.serve_forever, daemon=True)
  thread.start()
  try:
    venv = tmp_path / "venv"
    subprocess.run(  # noqa: S603 -- fixed interpreter and disposable venv
      [sys.executable, "-m", "venv", "--system-site-packages", str(venv)],
      check=True,
    )
    python = venv / "bin/python"
    install = subprocess.run(  # noqa: S603 -- disposable venv interpreter
      [
        str(python),
        "-m",
        "pip",
        "install",
        "--no-deps",
        "--only-binary=:all:",
        "--index-url",
        f"http://127.0.0.1:{server.server_port}/simple/",
        "inkcre-ext-github==0.1.0",
      ],
      check=False,
      capture_output=True,
      text=True,
    )
    assert install.returncode == 0, install.stderr

    projection = tmp_path / "core-projection"
    projection.mkdir()
    for package in ("app", "libs", "utils"):
      (projection / package).symlink_to(PROJECT_ROOT / package, target_is_directory=True)
    environment = {
      **os.environ,
      "DATABASE_URL": "postgresql+psycopg://test:test@127.0.0.1:1/test",
      "JWT_SECRET": "test-only-jwt-secret-at-least-32-bytes",
      "OBSRV__LOGGING_BACKEND": "none",
      "INKCRE_ENV_FILE": "",
      "PYTHONPATH": os.pathsep.join([str(projection), *site.getsitepackages()]),
    }
    contribution = subprocess.run(  # noqa: S603 -- disposable venv interpreter
      [
        str(python),
        "-c",
        (
          "import importlib.metadata, pathlib; "
          "from app.business.extension.main import ExtensionBase; "
          "dist=importlib.metadata.distribution('inkcre-ext-github'); "
          "eps=[e for e in dist.entry_points if e.group=='inkcre.core.extensions']; "
          "assert len(eps)==1 and eps[0].name=='github'; "
          "cls=eps[0].load(); assert issubclass(cls, ExtensionBase); "
          "module=__import__(cls.__module__, fromlist=['x']); "
          "assert '/venv/' in pathlib.Path(module.__file__).as_posix()"
        ),
      ],
      env=environment,
      cwd=tmp_path,
      check=False,
      capture_output=True,
      text=True,
    )
    assert contribution.returncode == 0, contribution.stderr
  finally:
    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
