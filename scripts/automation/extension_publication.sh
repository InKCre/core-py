#!/usr/bin/env bash

source "$(dirname "$0")/_common.sh"

if [ "${1:-}" != select ]; then
  echo "unknown Extension selection command: ${1:-}" >&2
  exit 2
fi

for name in EVENT_NAME EXTENSION; do require_env "$name"; done
selected=false
release_status() {
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
  curl --retry 2 --retry-delay 1 --retry-all-errors \
    --connect-timeout 10 --max-time 30 \
    --silent --output /dev/null --write-out '%{http_code}' \
    "$INKCRE_EXTENSION_REGISTRY_URL/v1/extensions/$namespace/$name/releases/$version"
}

if [ "$EVENT_NAME" = workflow_dispatch ]; then
  require_env REQUESTED_EXTENSION
  test "${INITIAL_PUBLICATION:-}" = INITIAL_ONLY
  if [ "$EXTENSION" = "$REQUESTED_EXTENSION" ]; then selected=true; fi
  if [ "$selected" = true ]; then
    require_env INKCRE_EXTENSION_REGISTRY_URL
    status="$(release_status)"
    if [ "$status" != 404 ]; then
      echo "INITIAL_ONLY requires an unpublished Release; Registry returned HTTP $status" >&2
      exit 1
    fi
  fi
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
    status="$(release_status)"
    case "$status" in
      200) ;;
      404) selected=true ;;
      *) echo "registry release lookup returned HTTP $status" >&2; exit 1 ;;
    esac
  fi
fi

emit_output selected "$selected"
