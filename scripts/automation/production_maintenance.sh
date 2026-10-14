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
      python -m scripts.automation.production_preflight
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
  backup-branch)
    for name in NEON_API_KEY NEON_BRANCH_ID NEON_PROJECT_ID GITHUB_RUN_ID HEAD_SHA \
      MIGRATION_DATABASE_URL; do
      require_env "$name"
    done

    flush_lsn="$(docker run --rm --env MIGRATION_DATABASE_URL \
      "inkcre-production-web:$HEAD_SHA" \
      python -m scripts.automation.production_preflight flush-lsn)"
    if [[ ! "$flush_lsn" =~ ^[0-9A-Fa-f]+/[0-9A-Fa-f]+$ ]]; then
      echo "PostgreSQL returned an invalid WAL flush LSN" >&2
      exit 1
    fi

    branch_name="core-py-maintenance-$GITHUB_RUN_ID"
    api="https://console.neon.tech/api/v2/projects/$NEON_PROJECT_ID"
    project="$(curl --fail --silent --show-error \
      --header "Authorization: Bearer $NEON_API_KEY" \
      --header 'Accept: application/json' \
      "https://console.neon.tech/api/v2/projects/$NEON_PROJECT_ID")"
    branches="$(curl --fail --silent --show-error \
      --header "Authorization: Bearer $NEON_API_KEY" \
      --header 'Accept: application/json' \
      "$api/branches?limit=100")"
    branch_count="$(jq -er '.branches | if type == "array" then length else error("invalid branches response") end' <<<"$branches")"
    branch_limit="$(jq -er '.project.owner.branches_limit | numbers' <<<"$project")"
    if [ "$branch_count" -gt "$((branch_limit - 2))" ]; then
      echo "Neon branch quota cannot reserve both the maintenance backup and a preserved recovery branch" >&2
      exit 1
    fi

    matches="$(jq -c --arg name "$branch_name" \
      '[.branches[] | select(.name == $name)]' <<<"$branches")"
    if [ "$(jq 'length' <<<"$matches")" -ne 0 ]; then
      echo "A Neon branch already uses this maintenance run name; refusing to reuse or overwrite it" >&2
      exit 1
    fi

    response_file="$(mktemp)"
    trap 'rm -f "$response_file"' EXIT
    request_body="$(jq -cn --arg name "$branch_name" --arg parent "$NEON_BRANCH_ID" \
      --arg lsn "$flush_lsn" '{branch:{name:$name,parent_id:$parent,parent_lsn:$lsn}}')"
    curl_exit=0
    http_status="$(curl --silent --show-error --output "$response_file" \
      --write-out '%{http_code}' --request POST \
      --header "Authorization: Bearer $NEON_API_KEY" \
      --header 'Accept: application/json' \
      --header 'Content-Type: application/json' \
      --data "$request_body" "$api/branches")" || curl_exit=$?
    if [ "$curl_exit" -ne 0 ]; then
      echo "Neon backup branch request failed before receiving an HTTP response (curl exit $curl_exit); inspect the branch list before any new run" >&2
      exit "$curl_exit"
    fi
    case "$http_status" in
      2[0-9][0-9]) ;;
      *)
        provider_error="$(jq -r '
          [
            (.code // .error.code // empty | tostring),
            (.message // .error.message // .detail // .error // "no provider message"
             | if type == "string" then . else tojson end)
          ]
          | map(select(length > 0) | gsub("[\\r\\n\\t]"; " ") | .[0:500])
          | join(": ")
        ' "$response_file" 2>/dev/null || printf 'non-JSON error response')"
        printf 'Neon backup branch request returned HTTP %s: %s\n' \
          "$http_status" "$provider_error" >&2
        exit 1
        ;;
    esac
    created="$(cat "$response_file")"
    jq -e --arg name "$branch_name" --arg parent "$NEON_BRANCH_ID" \
      --arg lsn "$flush_lsn" \
      '.branch.name == $name and .branch.parent_id == $parent and
       .branch.parent_lsn == $lsn and
       (.branch.id | type == "string" and length > 0) and
       ((.endpoints // []) | length == 0)' <<<"$created" >/dev/null
    backup_branch_id="$(jq -r '.branch.id' <<<"$created")"
    operation_ids="$(jq -r '(.operations // []) | if type == "array" then .[].id else error("invalid operations response") end' <<<"$created")"
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
            echo "Neon backup branch operation ended with status $operation_status" >&2
            exit 1
            ;;
        esac
        sleep 5
      done
      if [ "$operation_status" != finished ]; then
        echo "Timed out waiting for Neon backup branch operation" >&2
        exit 1
      fi
    done <<<"$operation_ids"

    backup_branch="$(curl --fail --silent --show-error \
      --header "Authorization: Bearer $NEON_API_KEY" \
      --header 'Accept: application/json' \
      "$api/branches/$backup_branch_id")"
    jq -e --arg id "$backup_branch_id" --arg name "$branch_name" \
      --arg parent "$NEON_BRANCH_ID" --arg lsn "$flush_lsn" \
      '.branch.id == $id and .branch.name == $name and
       .branch.parent_id == $parent and .branch.parent_lsn == $lsn and
       .branch.default == false and (.branch.expires_at == null)' \
      <<<"$backup_branch" >/dev/null
    endpoints="$(curl --fail --silent --show-error \
      --header "Authorization: Bearer $NEON_API_KEY" \
      --header 'Accept: application/json' \
      "$api/endpoints?limit=100")"
    jq -e --arg branch "$backup_branch_id" \
      '[.endpoints[] | select(.branch_id == $branch)] | length == 0' \
      <<<"$endpoints" >/dev/null
    emit_output backup_branch_id "$backup_branch_id"
    emit_output backup_branch_lsn "$flush_lsn"
    append_summary <<EOF
### Production maintenance recovery branch

- Neon branch: \`$NEON_BRANCH_ID\`
- Backup branch: \`$branch_name\` (\`$backup_branch_id\`)
- Parent LSN: \`$flush_lsn\`
- The backup has no compute endpoint or expiration. Migration is permitted only after this exact branch is confirmed.
EOF
    ;;
  *)
    echo "usage: $0 read-only-inventory|stop-services|backup-branch" >&2
    exit 2
    ;;
esac
