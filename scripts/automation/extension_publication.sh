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
          "$INKCRE_EXTENSION_REGISTRY_URL/v1/extensions/$namespace/$name/releases/$version")"
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
    namespace="${coordinate%%/*}"
    name="${coordinate#*/}"
    curl --fail-with-body --silent --show-error --request POST \
      --header "Authorization: Bearer $INKCRE_EXTENSION_REGISTRY_TOKEN" \
      --header "Content-Type: application/json" --data "$(jq -c '.prepare' "$METADATA")" \
      "$INKCRE_EXTENSION_REGISTRY_URL/v1/extensions/$namespace/$name/releases"
    ;;
  publish)
    for name in INKCRE_EXTENSION_REGISTRY_TOKEN INKCRE_EXTENSION_REGISTRY_URL METADATA; do
      require_env "$name"
    done
    coordinate="$(jq -r '.coordinate' "$METADATA")"
    version="$(jq -r '.version' "$METADATA")"
    namespace="${coordinate%%/*}"
    name="${coordinate#*/}"
    curl --fail-with-body --silent --show-error --request POST \
      --header "Authorization: Bearer $INKCRE_EXTENSION_REGISTRY_TOKEN" \
      "$INKCRE_EXTENSION_REGISTRY_URL/v1/extensions/$namespace/$name/releases/$version/publish"
    ;;
  verify)
    require_env INKCRE_EXTENSION_REGISTRY_URL
    require_env METADATA
    coordinate="$(jq -r '.coordinate' "$METADATA")"
    version="$(jq -r '.version' "$METADATA")"
    namespace="${coordinate%%/*}"
    name="${coordinate#*/}"
    curl --retry 2 --retry-delay 1 --retry-all-errors \
      --connect-timeout 10 --max-time 30 --fail --silent --show-error \
      "$INKCRE_EXTENSION_REGISTRY_URL/v1/extensions/$namespace/$name/releases/$version" |
      jq --exit-status --arg coordinate "$coordinate" --arg version "$version" \
        '.name == $coordinate and .version == $version and
         .state == "published" and .python.host_sdk == "core-py"'
    ;;
  *) echo "unknown Extension publication command: ${1:-}" >&2; exit 2 ;;
esac
