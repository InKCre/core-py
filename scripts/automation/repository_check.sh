#!/usr/bin/env bash

source "$(dirname "$0")/_common.sh"

case "${1:-}" in
  release-intent)
    arguments=()
    if [[ "${BASE_REVISION:-}" =~ ^[0-9a-f]{40}$ ]] &&
      [ "$BASE_REVISION" != 0000000000000000000000000000000000000000 ]; then
      arguments+=(--base "$BASE_REVISION")
    fi
    if [ "${RELEASE_PR:-false}" = true ]; then arguments+=(--release-pr); fi
    if [ "${MERGED_CHANGE:-false}" = true ]; then arguments+=(--merged); fi
    pdm run check:releases "${arguments[@]}"
    ;;
  extension-wheels)
    for extension in $(pdm run python scripts/release.py projects --extensions-only); do
      output="${RUNNER_TEMP:-/tmp}/wheels/$extension"
      mkdir --parents "$output"
      pdm run python -m build --wheel --no-isolation --outdir "$output" \
        "extensions/$extension"
      wheel="$(find "$output" -maxdepth 1 -type f -name '*.whl')"
      test "$(find "$output" -maxdepth 1 -type f -name '*.whl' | wc -l)" = 1
      pdm run python scripts/extension_distribution.py verify-wheel \
        --project "extensions/$extension" --wheel "$wheel"
    done
    ;;
  *) echo "usage: $0 release-intent|extension-wheels" >&2; exit 2 ;;
esac
