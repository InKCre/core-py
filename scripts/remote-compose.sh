#!/bin/sh
set -eu

payload_dir=$1
set -a
. "$payload_dir/compose.env"
set +a

set --
while IFS= read -r argument || [ -n "$argument" ]; do
  set -- "$@" "$argument"
done < "$payload_dir/compose.args"

docker_bin=${INKCRE_REMOTE_DOCKER_BIN:-docker}
if [ "${1:-}" = "__provider-check__" ]; then
  "$docker_bin" info --format '{{.ID}}{{println}}{{.Name}}{{println}}{{.ServerVersion}}'
  "$docker_bin" compose version --short
  exit 0
fi

compose_file="$payload_dir/database.compose.yml"
environment_file="$payload_dir/compose.env"
case "$docker_bin" in
  *.exe)
    compose_file=$(wslpath -w "$compose_file")
    environment_file=$(wslpath -w "$environment_file")
    ;;
esac

"$docker_bin" compose \
  --file "$compose_file" \
  --env-file "$environment_file" \
  --project-name "$INKCRE_COMPOSE_PROJECT_NAME" \
  "$@"
