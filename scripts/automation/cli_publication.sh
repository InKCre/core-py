#!/usr/bin/env bash

source "$(dirname "$0")/_common.sh"

case "${1:-}" in
  select)
    require_env EVENT_NAME
    if [ "$EVENT_NAME" = workflow_dispatch ]; then
      version="$(python3 -c 'import tomllib; print(tomllib.load(open("cli/pyproject.toml", "rb"))["project"]["version"])')"
      if [ "$version" = 0.0.0 ]; then
        echo "CLI 尚未经过 Release PR 准备，不能发布开发版本。" >&2
        exit 1
      fi
      selected=true
    else
      require_env BEFORE_SHA
      if [ "$BEFORE_SHA" = 0000000000000000000000000000000000000000 ]; then
        selected=false
      else
        selected="$(python3 scripts/release.py version-changed --project cli --base "$BEFORE_SHA")"
      fi
    fi
    emit_output selected "$selected"
    ;;
  check-build)
    pdm lock -p cli --check
    pdm install -p cli --frozen-lockfile
    pdm run -p cli check
    pdm build -p cli
    ;;
  publish)
    # PDM owns GitHub OIDC and PyPI upload/recovery; never rebuild after validation.
    pdm publish -p cli --no-build --skip-existing
    ;;
  *) echo "unknown CLI publication command: ${1:-}" >&2; exit 2 ;;
esac
