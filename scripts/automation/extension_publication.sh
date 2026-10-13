#!/usr/bin/env bash

source "$(dirname "$0")/_common.sh"

case "${1:-}" in
  discover)
    projects="$(python3 scripts/release.py projects --extensions-only --json)"
    if [ "${EVENT_NAME:-}" = workflow_dispatch ]; then
      require_env REQUESTED_EXTENSION
      python3 scripts/release.py projects --extensions-only |
        grep --fixed-strings --line-regexp -- "$REQUESTED_EXTENSION"
    fi
    emit_output projects "$projects"
    ;;
  verify-main-history)
    git fetch --no-tags origin main
    git merge-base --is-ancestor HEAD origin/main
    ;;
  select)
    for name in EVENT_NAME EXTENSION; do require_env "$name"; done
    selected=false
    if [ "$EVENT_NAME" = workflow_dispatch ]; then
      require_env REQUESTED_EXTENSION
      test "${INITIAL_PUBLICATION:-}" = INITIAL_ONLY
      if [ "$EXTENSION" = "$REQUESTED_EXTENSION" ]; then selected=true; fi
    else
      require_env BEFORE_SHA
      before="$BEFORE_SHA"
      [[ "$before" =~ ^[0-9a-f]{40}$ ]]
      if [ "$before" = 0000000000000000000000000000000000000000 ]; then
        selected=true
      else
        git merge-base --is-ancestor "$before" HEAD
        selected="$(python3 scripts/release.py version-changed \
          --project "$EXTENSION" --base "$before")"
      fi
      if [ "$selected" = false ]; then
        require_env INKCRE_EXTENSION_REGISTRY_URL
        read -r coordinate version < <(
          python3 - "$EXTENSION" <<'PY'
import sys

from scripts.release import project_by_key

project = project_by_key(sys.argv[1])
print(project.coordinate, project.version)
PY
        )
        namespace="${coordinate%%/*}"
        name="${coordinate#*/}"
        status="$(curl --retry 2 --retry-delay 1 --retry-all-errors \
          --connect-timeout 10 --max-time 30 \
          --silent --output /dev/null --write-out '%{http_code}' \
          "$INKCRE_EXTENSION_REGISTRY_URL/v2/extensions/$namespace/$name/distributions/python/releases/$version")"
        case "$status" in
          200) ;;
          404) selected=true ;;
          *) echo "registry release lookup returned HTTP $status" >&2; exit 1 ;;
        esac
      fi
    fi
    emit_output selected "$selected"
    ;;
  build)
    for name in EXTENSION GITHUB_REPOSITORY GITHUB_RUN_ID GITHUB_SERVER_URL; do
      require_env "$name"
    done
    output="$(mktemp -d "${RUNNER_TEMP:-/tmp}/$EXTENSION.XXXXXX")"
    mkdir --parents "$output/raw" "$output/finalized"
    pdm run python -m build --wheel --no-isolation --outdir "$output/raw" \
      "extensions/$EXTENSION"
    wheel="$(find "$output/raw" -maxdepth 1 -type f -name '*.whl')"
    test -n "$wheel"
    test "$(find "$output/raw" -maxdepth 1 -type f -name '*.whl' | wc -l)" = 1
    # The runtime reads the Toolkit manifest inside .dist-info, not registry metadata.
    # Match the preview path before verification and upload; never publish the raw wheel.
    pdm run inkcre-ext python wheel finalize \
      --project "extensions/$EXTENSION/pyproject.toml" --wheel "$wheel" \
      --output-dir "$output/finalized"
    wheel="$(find "$output/finalized" -maxdepth 1 -type f -name '*.whl')"
    test "$(find "$output/finalized" -maxdepth 1 -type f -name '*.whl' | wc -l)" = 1
    metadata="${RUNNER_TEMP:-/tmp}/$EXTENSION-metadata.json"
    pdm run python scripts/extension_distribution.py verify-wheel \
      --project "extensions/$EXTENSION" --wheel "$wheel"
    pdm run python scripts/extension_distribution.py metadata \
      --project "extensions/$EXTENSION" \
      --source-repository "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY" \
      --source-revision "$(git rev-parse HEAD)" --build-id "$GITHUB_RUN_ID" > "$metadata"
    emit_output metadata "$metadata"
    emit_output wheel "$wheel"
    ;;
  save-candidate)
    for name in CANDIDATE_ROOT EXTENSION GITHUB_RUN_ID GITHUB_SHA SELECTED; do
      require_env "$name"
    done
    mkdir -p "$CANDIDATE_ROOT"
    if [ -n "$(find "$CANDIDATE_ROOT" -mindepth 1 -print -quit)" ]; then
      echo "Candidate directory is not empty; refusing to replace saved release bytes." >&2
      exit 1
    fi
    if [ "$SELECTED" != true ]; then
      jq -n --arg extension "$EXTENSION" --arg run_id "$GITHUB_RUN_ID" \
        --arg source_revision "$GITHUB_SHA" \
        '{selected:false,extension:$extension,run_id:$run_id,source_revision:$source_revision}' \
        > "$CANDIDATE_ROOT/candidate.json"
      exit 0
    fi
    for name in METADATA WHEEL; do require_env "$name"; done
    test -f "$METADATA"
    test -f "$WHEEL"
    source_revision="$(jq -er '.prepare.python.source_revision' "$METADATA")"
    build_id="$(jq -er '.prepare.python.build_id' "$METADATA")"
    test "$source_revision" = "$GITHUB_SHA"
    test "$build_id" = "$GITHUB_RUN_ID"
    wheel_name="$(basename "$WHEEL")"
    cp "$METADATA" "$CANDIDATE_ROOT/metadata.json"
    cp "$WHEEL" "$CANDIDATE_ROOT/$wheel_name"
    wheel_sha256="$(shasum -a 256 "$CANDIDATE_ROOT/$wheel_name" | cut -d ' ' -f 1)"
    printf '%s\n' "$wheel_sha256" > "$CANDIDATE_ROOT/wheel.sha256"
    jq -n --arg extension "$EXTENSION" --arg run_id "$GITHUB_RUN_ID" \
      --arg source_revision "$source_revision" --arg wheel "$wheel_name" \
      --arg wheel_sha256 "$wheel_sha256" \
      '{selected:true,extension:$extension,run_id:$run_id,source_revision:$source_revision,wheel:$wheel,wheel_sha256:$wheel_sha256,metadata:"metadata.json"}' \
      > "$CANDIDATE_ROOT/candidate.json"
    ;;
  locate-artifact)
    for name in ARTIFACT_NAME GH_TOKEN GITHUB_REPOSITORY GITHUB_RUN_ID; do
      require_env "$name"
    done
    artifact_ids="$(gh api \
      --paginate \
      "/repos/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID/artifacts" \
      --jq '.artifacts[] | select(.name == env.ARTIFACT_NAME and .expired == false) | .id')"
    count="$(printf '%s\n' "$artifact_ids" | sed '/^$/d' | wc -l | tr -d ' ')"
    if [ "$count" != 1 ]; then
      echo "Expected one unexpired saved candidate artifact named $ARTIFACT_NAME; found $count. Do not rebuild this release." >&2
      exit 1
    fi
    emit_output artifact_id "$artifact_ids"
    ;;
  restore-candidate)
    for name in CANDIDATE_ROOT EXTENSION GITHUB_RUN_ID GITHUB_SHA; do
      require_env "$name"
    done
    manifest="$CANDIDATE_ROOT/candidate.json"
    test -f "$manifest"
    test "$(jq -er '.extension' "$manifest")" = "$EXTENSION"
    test "$(jq -er '.run_id' "$manifest")" = "$GITHUB_RUN_ID"
    test "$(jq -er '.source_revision' "$manifest")" = "$GITHUB_SHA"
    selected="$(jq -er '
      if (.selected | type) == "boolean" then
        .selected | tostring
      else
        error("candidate selected must be a boolean")
      end
    ' "$manifest")"
    emit_output selected "$selected"
    if [ "$selected" != true ]; then exit 0; fi

    wheel_name="$(jq -er '.wheel' "$manifest")"
    metadata_name="$(jq -er '.metadata' "$manifest")"
    expected_sha256="$(jq -er '.wheel_sha256' "$manifest")"
    [[ "$wheel_name" =~ ^[A-Za-z0-9_.+-]+\.whl$ ]]
    [[ "$expected_sha256" =~ ^[0-9a-f]{64}$ ]]
    test -f "$CANDIDATE_ROOT/$wheel_name"
    test -f "$CANDIDATE_ROOT/$metadata_name"
    actual_sha256="$(shasum -a 256 "$CANDIDATE_ROOT/$wheel_name" | cut -d ' ' -f 1)"
    test "$actual_sha256" = "$expected_sha256"
    metadata_revision="$(jq -er '.prepare.python.source_revision' "$CANDIDATE_ROOT/$metadata_name")"
    metadata_build_id="$(jq -er '.prepare.python.build_id' "$CANDIDATE_ROOT/$metadata_name")"
    test "$metadata_revision" = "$GITHUB_SHA"
    test "$metadata_build_id" = "$GITHUB_RUN_ID"
    test "$(jq -er '.distribution' "$CANDIDATE_ROOT/$metadata_name")" = python
    emit_output wheel "$CANDIDATE_ROOT/$wheel_name"
    emit_output metadata "$CANDIDATE_ROOT/$metadata_name"
    ;;
  revalidate)
    require_env EXTENSION
    git fetch --no-tags origin main
    git merge-base --is-ancestor HEAD origin/main
    python3 scripts/release.py verify-artifact-unchanged \
      --project "$EXTENSION" --from HEAD --to origin/main
    ;;
  prepare)
    for name in INKCRE_EXTENSION_REGISTRY_TOKEN INKCRE_EXTENSION_REGISTRY_URL METADATA; do
      require_env "$name"
    done
    coordinate="$(jq -r '.coordinate' "$METADATA")"
    distribution="$(jq -er '.distribution' "$METADATA")"
    test "$distribution" = python
    namespace="${coordinate%%/*}"
    name="${coordinate#*/}"
    curl --fail-with-body --silent --show-error --request POST \
      --header "Authorization: Bearer $INKCRE_EXTENSION_REGISTRY_TOKEN" \
      --header "Content-Type: application/json" --data "$(jq -c '.prepare' "$METADATA")" \
      "$INKCRE_EXTENSION_REGISTRY_URL/v2/extensions/$namespace/$name/distributions/$distribution/releases"
    ;;
  publish)
    for name in INKCRE_EXTENSION_REGISTRY_TOKEN INKCRE_EXTENSION_REGISTRY_URL METADATA; do
      require_env "$name"
    done
    coordinate="$(jq -r '.coordinate' "$METADATA")"
    version="$(jq -r '.version' "$METADATA")"
    distribution="$(jq -er '.distribution' "$METADATA")"
    test "$distribution" = python
    namespace="${coordinate%%/*}"
    name="${coordinate#*/}"
    curl --fail-with-body --silent --show-error --request POST \
      --header "Authorization: Bearer $INKCRE_EXTENSION_REGISTRY_TOKEN" \
      "$INKCRE_EXTENSION_REGISTRY_URL/v2/extensions/$namespace/$name/distributions/$distribution/releases/$version/publish"
    ;;
  verify)
    require_env INKCRE_EXTENSION_REGISTRY_URL
    require_env METADATA
    coordinate="$(jq -r '.coordinate' "$METADATA")"
    version="$(jq -r '.version' "$METADATA")"
    distribution="$(jq -er '.distribution' "$METADATA")"
    project="$(jq -er '.project' "$METADATA")"
    test "$distribution" = python
    namespace="${coordinate%%/*}"
    name="${coordinate#*/}"
    curl --retry 2 --retry-delay 1 --retry-all-errors \
      --connect-timeout 10 --max-time 30 --fail --silent --show-error \
      "$INKCRE_EXTENSION_REGISTRY_URL/v2/extensions/$namespace/$name/distributions/$distribution/releases/$version" |
      jq --exit-status --arg coordinate "$coordinate" --arg version "$version" \
        --arg project "$project" \
        '.name == $coordinate and .version == $version and
         .distribution == "python" and .state == "published" and
         .python.project == $project and .python.host_sdk == "core-py" and
         .module_federation == null'
    ;;
  *) echo "unknown Extension publication command: ${1:-}" >&2; exit 2 ;;
esac
