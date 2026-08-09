"""Container and exact-main delivery contract for admitted Extension targets."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")
PUBLISH_WORKFLOW = (PROJECT_ROOT / ".github/workflows/artifact-publish.yml").read_text(
  encoding="utf-8"
)
PRODUCTION_WORKFLOW = (PROJECT_ROOT / ".github/workflows/production-deploy.yml").read_text(
  encoding="utf-8"
)


def _ordered_positions(document: str, *needles: str) -> list[int]:
  positions = [document.index(needle) for needle in needles]
  assert positions == sorted(positions)
  return positions


def test_service_image_copies_the_complete_generated_target_tree() -> None:
  service = DOCKERFILE.split("FROM runtime AS service", 1)[1].split(
    "FROM service AS heroku-release", 1
  )[0]

  assert (
    "COPY --chown=inkcre:inkcre release/extension-targets/ /app/extension-targets/"
  ) in service
  assert (
    'io.inkcre.extension-targets.catalog="/app/extension-targets/catalog.json"' in service
  )
  assert "find /app/extension-targets -type d -exec chmod 0755 {} +" in service
  assert "find /app/extension-targets -type f -exec chmod 0644 {} +" in service
  assert DOCKERFILE.index("USER inkcre") < DOCKERFILE.index("FROM runtime AS service")


def test_generated_digest_artifacts_are_not_source_control_inputs() -> None:
  ignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
  marker = PROJECT_ROOT / "release/extension-targets/README.md"

  assert "release/extension-targets/*" in ignore
  assert "!release/extension-targets/README.md" in ignore
  assert marker.is_file()


def test_target_publisher_uses_python312_and_the_frozen_cd_group() -> None:
  pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
  lock = (PROJECT_ROOT / "pdm.lock").read_text(encoding="utf-8")

  assert "pdm-project/setup-pdm@973541a5febeafcfdadf8a51211435be6ecfd90f" in (
    PUBLISH_WORKFLOW
  )
  assert "python-version-file: .python-version" in PUBLISH_WORKFLOW
  assert "version: 2.27.0" in PUBLISH_WORKFLOW
  assert "--no-default" in PUBLISH_WORKFLOW
  assert "--group extension-publisher" in PUBLISH_WORKFLOW
  assert "--frozen-lockfile" in PUBLISH_WORKFLOW
  assert "pdm run which inkcre-ext" in PUBLISH_WORKFLOW
  assert "extension-publisher = [" in pyproject
  assert "inkcre-extension-registry[cli]" in pyproject
  assert 'groups = ["default", "dev", "extension-publisher"]' in lock
  assert 'extras = ["cli"]' in lock
  assert "ac8771ba3a92b5e50deee1ea6f5a81511b3e0f4d716c60e24d873c99b9641e56" in lock


def test_exact_main_delivery_orders_target_image_publish_and_promotion() -> None:
  assert "github.event.workflow_run.conclusion == 'success'" in PUBLISH_WORKFLOW
  assert "github.event.workflow_run.event == 'push'" in PUBLISH_WORKFLOW
  assert "github.event.workflow_run.head_branch == 'main'" in PUBLISH_WORKFLOW
  assert 'test "$(git rev-parse origin/main)" = "$HEAD_SHA"' in PUBLISH_WORKFLOW

  _ordered_positions(
    PUBLISH_WORKFLOW,
    "scripts/build_extension_target.py bundle",
    '"${{ steps.publisher.outputs.cli }}" build-target',
    "scripts/build_extension_target.py catalog",
    "docker build \\",
    'docker push "$commit_ref"',
    '"${{ steps.publisher.outputs.cli }}" publish-target',
    'docker tag "$COMMIT_REF" "$IMAGE:main"',
    'docker push "$IMAGE:main"',
  )
  assert "if: steps.registry.outcome == 'success'" in PUBLISH_WORKFLOW
  assert "continue-on-error" not in PUBLISH_WORKFLOW


def test_registry_publish_uses_only_scoped_secret_and_exact_provenance() -> None:
  assert PUBLISH_WORKFLOW.count("${{ secrets.INKCRE_EXTENSION_REGISTRY_TOKEN }}") == 1
  assert "--token" not in PUBLISH_WORKFLOW
  assert (
    "${{ vars.INKCRE_EXTENSION_REGISTRY_URL || "
    "'https://inkcre-extension-registry.lanzhijiang.workers.dev' }}"
  ) in PUBLISH_WORKFLOW
  assert "BUILD_ID: ${{ github.run_id }}" in PUBLISH_WORKFLOW
  assert "SOURCE_REPOSITORY: ${{ github.server_url }}/${{ github.repository }}" in (
    PUBLISH_WORKFLOW
  )
  assert '--source-revision "$HEAD_SHA"' in PUBLISH_WORKFLOW
  assert '--build-id "$BUILD_ID"' in PUBLISH_WORKFLOW
  assert '"${{ steps.publisher.outputs.cli }}" show-release' in PUBLISH_WORKFLOW
  assert PUBLISH_WORKFLOW.count(".source_repository == $source_repository") == 1
  assert '.source_revision | type == "string" and length > 0' in PUBLISH_WORKFLOW
  assert ".source_revision == $source_revision" not in PUBLISH_WORKFLOW
  assert '.build_id | type == "string" and length > 0' in PUBLISH_WORKFLOW
  assert ".build_id == $build_id" not in PUBLISH_WORKFLOW
  assert '--directory "${{ steps.target.outputs.artifact_directory }}"' in PUBLISH_WORKFLOW


def test_delivery_checks_local_cli_catalog_image_and_published_digest() -> None:
  assert 'test "$target_digest" = "$cli_digest"' in PUBLISH_WORKFLOW
  assert 'test "$target_digest" = "$catalog_digest"' in PUBLISH_WORKFLOW
  assert 'test "$image_catalog_digest" = "$TARGET_DIGEST"' in PUBLISH_WORKFLOW
  assert 'test "$image_verified_digest" = "$TARGET_DIGEST"' in PUBLISH_WORKFLOW
  assert ".target_digest == $digest" in PUBLISH_WORKFLOW
  assert (
    'cmp "$published_manifest" release/extension-targets/twitter/manifest.json'
    in PUBLISH_WORKFLOW
  )
  assert "- Delivery source revision:" in PUBLISH_WORKFLOW
  assert "- Target source revision:" in PUBLISH_WORKFLOW
  assert "- Immutable image:" in PUBLISH_WORKFLOW
  assert "- Target digest:" in PUBLISH_WORKFLOW
  assert "- Target build ID:" in PUBLISH_WORKFLOW


def test_failed_artifact_publication_cannot_trigger_automatic_production() -> None:
  assert "- Publish runtime artifact" in PRODUCTION_WORKFLOW
  assert "github.event.workflow_run.conclusion == 'success'" in PRODUCTION_WORKFLOW
