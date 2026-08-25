#!/usr/bin/env bash

source "$(dirname "$0")/_common.sh"

case "${1:-}" in
  extension-intent)
    arguments=()
    if [[ "${BASE_REVISION:-}" =~ ^[0-9a-f]{40}$ ]] &&
      [ "$BASE_REVISION" != 0000000000000000000000000000000000000000 ]; then
      arguments+=(--base "$BASE_REVISION")
    fi
    pdm run check:extension-releases "${arguments[@]}"
    ;;
  extension-wheels)
    for extension in $(pdm run python scripts/extension_release.py projects); do
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
  *) echo "usage: $0 extension-intent|extension-wheels" >&2; exit 2 ;;
esac
