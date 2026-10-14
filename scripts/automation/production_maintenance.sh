#!/usr/bin/env bash

source "$(dirname "$0")/_common.sh"

case "${1:-}" in
  read-only-inventory)
    for name in HEROKU_API_KEY HEROKU_APP_NAME POSTGREST_APP_NAME \
      MIGRATION_DATABASE_URL APP_DATABASE_IDENTITY_URL HEAD_SHA CORE_IMAGE_DIGEST; do
      require_env "$name"
    done
    core_config="$(heroku config --app "$HEROKU_APP_NAME" --json)"
    postgrest_config="$(heroku config --app "$POSTGREST_APP_NAME" --json)"
    production_profile="$(cat deploy/profiles/production.json)"
    while IFS= read -r secret_value; do
      mask_value "$secret_value"
    done < <(jq -r '[.DATABASE_URL, .JWT_SECRET] | .[] | select(type == "string" and length > 0)' <<<"$core_config")
    while IFS= read -r secret_value; do
      mask_value "$secret_value"
    done < <(jq -r '[.PGRST_DB_URI, .PGRST_JWT_SECRET] | .[] | select(type == "string" and length > 0)' <<<"$postgrest_config")
    export CORE_CONFIG_JSON="$core_config"
    export POSTGREST_CONFIG_JSON="$postgrest_config"
    export PRODUCTION_PROFILE_JSON="$production_profile"
    export CORE_PEER_ID="$(jq -r '.PEER_ID' <<<"$core_config")"
    docker run --rm \
      --env MIGRATION_DATABASE_URL \
      --env APP_DATABASE_IDENTITY_URL \
      --env HEROKU_APP_NAME \
      --env CORE_PEER_ID \
      --env CORE_CONFIG_JSON \
      --env POSTGREST_CONFIG_JSON \
      --env PRODUCTION_PROFILE_JSON \
      --env HEAD_SHA \
      --env CORE_IMAGE_DIGEST \
      --env REQUIRE_QUIESCENT_DATABASE \
      "inkcre-production-web:$HEAD_SHA" \
      python scripts/automation/production_preflight.py
    ;;
  stop-services)
    for name in HEROKU_API_KEY HEROKU_APP_NAME POSTGREST_APP_NAME; do
      require_env "$name"
    done
    for app_name in "$HEROKU_APP_NAME" "$POSTGREST_APP_NAME"; do
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
        echo "Heroku app $app_name still has dynos after scaling web to zero" >&2
        exit 1
      fi
      printf '%s stopped; no Heroku dynos remain.\n' "$app_name"
    done
    ;;
  snapshot)
    for name in NEON_API_KEY NEON_BRANCH_ID NEON_PROJECT_ID GITHUB_RUN_ID; do
      require_env "$name"
    done
    snapshot_name="core-py-maintenance-$GITHUB_RUN_ID"
    api="https://console.neon.tech/api/v2/projects/$NEON_PROJECT_ID"
    snapshots="$(curl --fail --silent --show-error \
      --header "Authorization: Bearer $NEON_API_KEY" \
      --header 'Accept: application/json' \
      "$api/snapshots")"
    matches="$(jq -c --arg name "$snapshot_name" \
      '[.snapshots[] | select(.name == $name)]' <<<"$snapshots")"
    count="$(jq 'length' <<<"$matches")"
    if [ "$count" -gt 1 ]; then
      echo "More than one Neon snapshot has the maintenance run name; refusing ambiguity" >&2
      exit 1
    fi
    if [ "$count" -eq 1 ]; then
      snapshot_id="$(jq -r '.[0].id' <<<"$matches")"
      source_branch="$(jq -r '.[0].source_branch_id' <<<"$matches")"
      if [ "$source_branch" != "$NEON_BRANCH_ID" ]; then
        echo "Existing maintenance snapshot belongs to another Neon branch" >&2
        exit 1
      fi
    else
      expires_at="$(date -u -d '+30 days' '+%Y-%m-%dT%H:%M:%SZ')"
      created="$(curl --fail --silent --show-error --request POST \
        --header "Authorization: Bearer $NEON_API_KEY" \
        --header 'Accept: application/json' \
        "$api/branches/$NEON_BRANCH_ID/snapshot?name=$snapshot_name&expires_at=$expires_at")"
      jq -e --arg name "$snapshot_name" --arg branch "$NEON_BRANCH_ID" \
        '.snapshot.name == $name and .snapshot.source_branch_id == $branch and
         (.snapshot.id | type == "string" and length > 0)' \
        <<<"$created" >/dev/null
      snapshot_id="$(jq -r '.snapshot.id' <<<"$created")"
      while IFS= read -r operation_id; do
        [ -n "$operation_id" ] || continue
        operation_status=""
        for _ in $(seq 1 120); do
          operation="$(curl --fail --silent --show-error \
            --header "Authorization: Bearer $NEON_API_KEY" \
            --header 'Accept: application/json' \
            "$api/operations/$operation_id")"
          operation_status="$(jq -r '.operation.status' <<<"$operation")"
          case "$operation_status" in
            finished) break ;;
            failed|error|cancelled|skipped)
              echo "Neon snapshot operation ended with status $operation_status" >&2
              exit 1
              ;;
          esac
          sleep 5
        done
        if [ "$operation_status" != finished ]; then
          echo "Timed out waiting for Neon snapshot operation" >&2
          exit 1
        fi
      done < <(jq -r '.operations[].id' <<<"$created")
    fi
    snapshot="$(curl --fail --silent --show-error \
      --header "Authorization: Bearer $NEON_API_KEY" \
      --header 'Accept: application/json' \
      "$api/snapshots/$snapshot_id")"
    jq -e --arg id "$snapshot_id" --arg name "$snapshot_name" \
      --arg branch "$NEON_BRANCH_ID" \
      '.snapshot.id == $id and .snapshot.name == $name and
       .snapshot.source_branch_id == $branch' <<<"$snapshot" >/dev/null
    emit_output snapshot_id "$snapshot_id"
    append_summary <<EOF
### Production maintenance snapshot

- Neon branch: \`$NEON_BRANCH_ID\`
- Snapshot: \`$snapshot_name\` (\`$snapshot_id\`)
- Migration is permitted only after this exact snapshot is confirmed.
EOF
    ;;
  *)
    echo "usage: $0 read-only-inventory|stop-services|snapshot" >&2
    exit 2
    ;;
esac
