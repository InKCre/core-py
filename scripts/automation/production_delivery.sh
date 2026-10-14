#!/usr/bin/env bash

source "$(dirname "$0")/_common.sh"

wait_for_release() {
  local app_name="$1"
  local version="$2"
  local status
  for _ in $(seq 1 120); do
    status="$(
      heroku releases --app "$app_name" --json |
        jq -r --argjson version "$version" \
          '.[] | select(.version == $version) | .status'
    )"
    case "$status" in
      succeeded) return 0 ;;
      failed)
        heroku releases:output "v$version" --app "$app_name"
        return 1
        ;;
    esac
    sleep 5
  done
  echo "Timed out waiting for $app_name release v$version" >&2
  return 1
}

retry_command() {
  local max_attempts="$1"
  shift
  local attempt
  for attempt in $(seq 1 "$max_attempts"); do
    if "$@"; then
      return 0
    fi
    if [ "$attempt" -lt "$max_attempts" ]; then
      sleep "$((attempt * 2))"
    fi
  done
  return 1
}

latest_release() {
  heroku releases --app "$1" --json | jq -r '.[0].version // empty'
}

require_deployment_profile() {
  local app_name="$1" actual
  actual="$(heroku config:get INKCRE_DEPLOYMENT_PROFILE --app "$app_name" || true)"
  if [ "$actual" != "$EXPECTED_DEPLOYMENT_PROFILE" ]; then
    echo "Refusing existing Heroku app $app_name: deployment profile does not match" >&2
    return 1
  fi
}

wait_if_changed() {
  local app_name="$1"
  local before="$2"
  local after
  after="$(latest_release "$app_name")"
  if [ "$after" != "$before" ]; then
    wait_for_release "$app_name" "$after"
  fi
  printf '%s' "${after:-$before}"
}

transfer_process_images() {
  for name in APP_NAME HEROKU_API_KEY HEAD_SHA POSTGREST_APP_NAME; do
    require_env "$name"
  done

  for attempt in $(seq 1 5); do
    if printf '%s' "$HEROKU_API_KEY" |
      docker login --username=_ --password-stdin registry.heroku.com; then
      break
    fi
    test "$attempt" -lt 5
    sleep "$((attempt * 2))"
  done
  docker tag "inkcre-production-web:$HEAD_SHA" "registry.heroku.com/$APP_NAME/web"
  docker tag "inkcre-production-release:$HEAD_SHA" "registry.heroku.com/$APP_NAME/release"
  docker tag "inkcre-production-postgrest:$HEAD_SHA" \
    "registry.heroku.com/$POSTGREST_APP_NAME/web"
  push_and_verify_image "inkcre-production-web:$HEAD_SHA" \
    "registry.heroku.com/$APP_NAME/web"
  push_and_verify_image "inkcre-production-release:$HEAD_SHA" \
    "registry.heroku.com/$APP_NAME/release"
  push_and_verify_image "inkcre-production-postgrest:$HEAD_SHA" \
    "registry.heroku.com/$POSTGREST_APP_NAME/web"
}

verify_registry_image() {
  local source_image="$1"
  local registry_image="$2"
  local source_id remote_id
  source_id="$(docker image inspect --format='{{.Id}}' "$source_image")"
  docker pull "$registry_image" >/dev/null
  remote_id="$(docker image inspect --format='{{.Id}}' "$registry_image")"
  if [ "$source_id" != "$remote_id" ]; then
    echo "Heroku registry image $registry_image does not match source image $source_image" >&2
    return 1
  fi
  printf '%s registry image matches source image ID %s.\n' "$registry_image" "$remote_id"
}

push_and_verify_image() {
  local source_image="$1"
  local registry_image="$2"
  local attempt
  for attempt in $(seq 1 5); do
    if docker push "$registry_image" && verify_registry_image "$source_image" "$registry_image"; then
      return 0
    fi
    if [ "$attempt" -lt 5 ]; then sleep "$((attempt * 2))"; fi
  done
  echo "Could not verify Heroku registry image $registry_image against its source" >&2
  return 1
}

require_transferred_process_images() {
  require_env HEAD_SHA
  for pair in \
    "inkcre-production-web:$HEAD_SHA registry.heroku.com/$APP_NAME/web" \
    "inkcre-production-release:$HEAD_SHA registry.heroku.com/$APP_NAME/release" \
    "inkcre-production-postgrest:$HEAD_SHA registry.heroku.com/$POSTGREST_APP_NAME/web"; do
    read -r source_image registry_image <<<"$pair"
    verify_registry_image "$source_image" "$registry_image"
  done
}

stop_maintenance_apps_after_failed_probe() {
  for app_name in "$APP_NAME" "$POSTGREST_APP_NAME"; do
    app_json="$(heroku apps:info --app "$app_name" --json)"
    jq -e --arg expected "$app_name" '.app.name == $expected' \
      <<<"$app_json" >/dev/null
    heroku ps:scale web=0 --app "$app_name"
    stopped=false
    for _ in $(seq 1 60); do
      dynos="$(heroku ps --app "$app_name" --json)"
      if jq -e 'type == "array" and length == 0' <<<"$dynos" >/dev/null; then
        stopped=true
        break
      fi
      sleep 5
    done
    if [ "$stopped" != true ]; then
      echo "Could not confirm that maintenance app $app_name stopped after probe failure" >&2
      return 1
    fi
  done
  append_summary <<'EOF'
Maintenance probe failed; both apps were scaled to zero and verified with no remaining dynos.
EOF
}

case "${1:-}" in
  transfer-images)
    transfer_process_images
    ;;
  verify-transferred-images)
    for name in APP_NAME HEAD_SHA POSTGREST_APP_NAME; do require_env "$name"; done
    require_transferred_process_images
    ;;
  require-stopped-apps)
    for name in HEROKU_API_KEY APP_NAME POSTGREST_APP_NAME; do
      require_env "$name"
    done
    for app_name in "$APP_NAME" "$POSTGREST_APP_NAME"; do
      app_json="$(heroku apps:info --app "$app_name" --json)"
      jq -e --arg expected "$app_name" '.app.name == $expected' \
        <<<"$app_json" >/dev/null
      dynos="$(heroku ps --app "$app_name" --json)"
      if ! jq -e 'type == "array" and length == 0' <<<"$dynos" >/dev/null; then
        echo "Refusing database changes while Heroku app $app_name still has dynos" >&2
        exit 1
      fi
    done
    ;;
  resolve-neon)
    require_env NEON_API_KEY
    require_env NEON_BRANCH_ID
    require_env NEON_PROJECT_ID
    pooled_owner_database_url="$(
      npx --yes neonctl@2.36.0 connection-string "$NEON_BRANCH_ID" \
        --project-id "$NEON_PROJECT_ID" --role-name neondb_owner \
        --database-name neondb --pooled --no-color
    )"
    direct_owner_database_url="$(
      npx --yes neonctl@2.36.0 connection-string "$NEON_BRANCH_ID" \
        --project-id "$NEON_PROJECT_ID" --role-name neondb_owner \
        --database-name neondb --no-pooled --no-color
    )"
    mask_value "$pooled_owner_database_url"
    mask_value "$direct_owner_database_url"
    emit_output pooled_owner_database_url "$pooled_owner_database_url"
    emit_output direct_owner_database_url "$direct_owner_database_url"
    ;;
  resolve-apps)
    require_env HEROKU_API_KEY
    require_env HEROKU_APP_NAME
    require_env POSTGREST_APP_NAME
    core_app_created=false
    if [ "${REQUIRE_EXISTING_APPS:-false}" = true ]; then
      app_json="$(heroku apps:info --app "$HEROKU_APP_NAME" --json)" || {
        echo "Could not read configured production Heroku app $HEROKU_APP_NAME" >&2
        exit 1
      }
      postgrest_json="$(heroku apps:info --app "$POSTGREST_APP_NAME" --json)" || {
        echo "Could not read configured production Heroku app $POSTGREST_APP_NAME" >&2
        exit 1
      }
      for app in "$HEROKU_APP_NAME" "$POSTGREST_APP_NAME"; do
        if [ "$app" = "$HEROKU_APP_NAME" ]; then
          resolved_app_json="$app_json"
        else
          resolved_app_json="$postgrest_json"
        fi
        if ! jq -e --arg expected "$app" '.app.name == $expected' \
          <<<"$resolved_app_json" >/dev/null; then
          echo "Heroku returned an unexpected app identity for $app" >&2
          exit 1
        fi
      done
    else
      app_json="$(heroku apps:info --app "$HEROKU_APP_NAME" --json 2>/dev/null || true)"
      postgrest_json="$(heroku apps:info --app "$POSTGREST_APP_NAME" --json 2>/dev/null || true)"
    fi
    if [ -n "${EXPECTED_DEPLOYMENT_PROFILE:-}" ]; then
      if [ -n "$app_json" ]; then
        require_deployment_profile "$HEROKU_APP_NAME"
      fi
      if [ -n "$postgrest_json" ]; then
        require_deployment_profile "$POSTGREST_APP_NAME"
      fi
    fi
    if [ -z "$app_json" ]; then
      if [ "${REQUIRE_EXISTING_APPS:-false}" = true ]; then
        echo "Configured Heroku app $HEROKU_APP_NAME does not exist" >&2
        exit 1
      fi
      heroku apps:create "$HEROKU_APP_NAME" --region us --stack container
      app_json="$(heroku apps:info --app "$HEROKU_APP_NAME" --json)"
      core_app_created=true
      if [ -n "${EXPECTED_DEPLOYMENT_PROFILE:-}" ]; then
        heroku config:set --app "$HEROKU_APP_NAME" \
          "INKCRE_DEPLOYMENT_PROFILE=$EXPECTED_DEPLOYMENT_PROFILE" >/dev/null
      fi
    fi
    postgrest_app_created=false
    if [ -z "$postgrest_json" ]; then
      if [ "${REQUIRE_EXISTING_APPS:-false}" = true ]; then
        echo "Configured Heroku app $POSTGREST_APP_NAME does not exist" >&2
        exit 1
      fi
      heroku apps:create "$POSTGREST_APP_NAME" --region us --stack container
      postgrest_json="$(heroku apps:info --app "$POSTGREST_APP_NAME" --json)"
      postgrest_app_created=true
      if [ -n "${EXPECTED_DEPLOYMENT_PROFILE:-}" ]; then
        heroku config:set --app "$POSTGREST_APP_NAME" \
          "INKCRE_DEPLOYMENT_PROFILE=$EXPECTED_DEPLOYMENT_PROFILE" >/dev/null
      fi
    fi
    emit_output app_name "$HEROKU_APP_NAME"
    emit_output core_app_created "$core_app_created"
    emit_output postgrest_app_created "$postgrest_app_created"
    emit_output postgrest_app_name "$POSTGREST_APP_NAME"
    emit_output postgrest_url "$(jq -r '.app.web_url' <<<"$postgrest_json")"
    emit_output web_url "$(jq -r '.app.web_url' <<<"$app_json")"
    ;;
  converge-database)
    require_env CORE_DATABASE_PASSWORD
    require_env HEAD_SHA
    require_env MIGRATION_DATABASE_URL
    require_env POOLED_OWNER_DATABASE_URL
    require_env POSTGREST_DATABASE_PASSWORD
    docker run --rm --env CORE_DATABASE_PASSWORD --env MIGRATION_DATABASE_URL \
      --env POSTGREST_DATABASE_PASSWORD "inkcre-production-web:$HEAD_SHA" \
      python scripts/container.py db init --profile runtime \
        --environment "${DATABASE_ENVIRONMENT:-production}"
    docker run --rm --env MIGRATION_DATABASE_URL "inkcre-production-web:$HEAD_SHA" \
      python scripts/container.py db ready --profile runtime --json
    core_database_url="$(
      docker run --rm --env SOURCE_DATABASE_URL="$POOLED_OWNER_DATABASE_URL" \
        --env TARGET_DATABASE_PASSWORD="$CORE_DATABASE_PASSWORD" \
        --env TARGET_DATABASE_ROLE=inkcre_core --entrypoint python \
        "inkcre-production-web:$HEAD_SHA" scripts/rebind_database_url.py \
        --scheme postgresql+psycopg
    )"
    postgrest_database_url="$(
      docker run --rm --env SOURCE_DATABASE_URL="$POOLED_OWNER_DATABASE_URL" \
        --env TARGET_DATABASE_PASSWORD="$POSTGREST_DATABASE_PASSWORD" \
        --env TARGET_DATABASE_ROLE=authenticator --entrypoint python \
        "inkcre-production-web:$HEAD_SHA" scripts/rebind_database_url.py \
        --scheme postgresql
    )"
    mask_value "$core_database_url"
    mask_value "$postgrest_database_url"
    emit_output core_database_url "$core_database_url"
    emit_output postgrest_database_url "$postgrest_database_url"
    ;;
  release)
    for name in APP_NAME DATABASE_URL HEAD_SHA HEROKU_API_KEY JWT_SECRET \
      POSTGREST_APP_NAME POSTGREST_DATABASE_URL; do
      require_env "$name"
    done
    core_profile=()
    postgrest_profile=()
    if [ -n "${INKCRE_DEPLOYMENT_PROFILE:-}" ]; then
      core_profile+=("INKCRE_DEPLOYMENT_PROFILE=$INKCRE_DEPLOYMENT_PROFILE")
      postgrest_profile+=("INKCRE_DEPLOYMENT_PROFILE=$INKCRE_DEPLOYMENT_PROFILE")
    fi
    before="$(latest_release "$APP_NAME")"
    peer_id="$(python3 -c "import uuid; print(uuid.uuid5(uuid.NAMESPACE_URL, '$APP_NAME'))")"
    heroku config:set --app "$APP_NAME" \
      DATABASE_SCALE_0=true "DATABASE_URL=$DATABASE_URL" INKCRE_ENV_FILE= \
      "JWT_SECRET=$JWT_SECRET" OBSRV__LOGGING_BACKEND=postgresql "PEER_ID=$peer_id" \
      "PEER_NAME=${PEER_NAME:-core-py-production}" SKIP_EXTENSIONS_SYNC=0 \
      "${core_profile[@]}" >/dev/null
    heroku config:unset CLIENT_BASE_URL CLIENT_ID CLIENT_NAME LLM_SP_AK \
      LLM_SP_BASE_URL --app "$APP_NAME" >/dev/null || true
    if [ -n "$(heroku config:get MIGRATION_DATABASE_URL --app "$APP_NAME" || true)" ]; then
      heroku config:unset MIGRATION_DATABASE_URL --app "$APP_NAME" >/dev/null
    fi
    wait_if_changed "$APP_NAME" "$before" >/dev/null

    before="$(latest_release "$POSTGREST_APP_NAME")"
    heroku config:set --app "$POSTGREST_APP_NAME" \
      PGRST_DB_ANON_ROLE=anonymous PGRST_DB_POOL=2 \
      PGRST_DB_PRE_REQUEST=inkcre_internal.check_jwt PGRST_DB_SCHEMAS=inkcre \
      "PGRST_DB_URI=$POSTGREST_DATABASE_URL" PGRST_JWT_AUD=inkcre-api \
      "PGRST_JWT_SECRET=$JWT_SECRET" "${postgrest_profile[@]}" >/dev/null
    wait_if_changed "$POSTGREST_APP_NAME" "$before" >/dev/null

    if [ "${IMAGES_ALREADY_TRANSFERRED:-false}" = true ]; then
      require_transferred_process_images
    else
      transfer_process_images
    fi

    before="$(latest_release "$APP_NAME")"
    heroku container:release release --app "$APP_NAME"
    wait_if_changed "$APP_NAME" "$before" >/dev/null
    before="$(latest_release "$APP_NAME")"
    heroku container:release web --app "$APP_NAME"
    web_release="$(wait_if_changed "$APP_NAME" "$before")"
    before="$(latest_release "$POSTGREST_APP_NAME")"
    heroku container:release web --app "$POSTGREST_APP_NAME"
    postgrest_release="$(wait_if_changed "$POSTGREST_APP_NAME" "$before")"
    heroku ps:scale web=1:eco --app "$APP_NAME"
    heroku ps:scale web=1:eco --app "$POSTGREST_APP_NAME"
    emit_output core_local_image_id "$(docker image inspect --format='{{.Id}}' "inkcre-production-web:$HEAD_SHA")"
    emit_output web_release "$web_release"
    emit_output postgrest_release "$postgrest_release"
    ;;
  advertise)
    for name in APP_NAME DATABASE_URL HEAD_SHA WEB_URL; do require_env "$name"; done
    peer_id="$(python3 -c "import uuid; print(uuid.uuid5(uuid.NAMESPACE_URL, '$APP_NAME'))")"
    docker run --rm --env DATABASE_URL "inkcre-production-release:$HEAD_SHA" \
      python scripts/configure_peer_runtime.py --peer-id "$peer_id" \
      --http-public-base-url "$WEB_URL"
    ;;
  probe)
    for name in APP_NAME CORE_IMAGE_DIGEST CORE_LOCAL_IMAGE_ID HEAD_SHA \
      HEROKU_API_KEY JWT_SECRET POSTGREST_APP_NAME POSTGREST_RELEASE \
      POSTGREST_URL WEB_RELEASE WEB_URL; do
      require_env "$name"
    done
    for _ in $(seq 1 60); do
      if curl --fail --silent "${WEB_URL}livez" >/dev/null &&
        curl --fail --silent "${WEB_URL}readyz" >/dev/null &&
        docker run --rm --entrypoint python "inkcre-production-web:$HEAD_SHA" \
          scripts/verify_postgrest_contract.py --base-url "$POSTGREST_URL" \
          --jwt-secret "$JWT_SECRET" --wrong-jwt-secret "wrong-$JWT_SECRET"; then
        append_summary <<EOF
### ${DEPLOYMENT_SUMMARY_TITLE:-Heroku production}

- Core app: \`$APP_NAME\`
- Core URL: $WEB_URL
- PostgREST app: \`$POSTGREST_APP_NAME\`
- PostgREST URL: $POSTGREST_URL
- Commit: \`$HEAD_SHA\`
- ${CORE_IMAGE_LABEL:-GHCR candidate}: \`$CORE_IMAGE_DIGEST\`
- Transferred local image ID: \`$CORE_LOCAL_IMAGE_ID\`
- Heroku core release: \`v$WEB_RELEASE\`
- Heroku PostgREST release: \`v$POSTGREST_RELEASE\`
- Core liveness/readiness: ready
- PostgREST JWT read/write/deny contract: ready
- Formation: Eco
EOF
        exit 0
      fi
      sleep 5
    done
    heroku logs --num 200 --app "$APP_NAME" || true
    heroku logs --num 200 --app "$POSTGREST_APP_NAME" || true
    if [ "${MAINTENANCE_WINDOW:-false}" = true ]; then
      stop_maintenance_apps_after_failed_probe
    fi
    exit 1
    ;;
  *)
    echo "usage: $0 resolve-neon|resolve-apps|require-stopped-apps|transfer-images|verify-transferred-images|converge-database|release|advertise|probe" >&2
    exit 2
    ;;
esac
