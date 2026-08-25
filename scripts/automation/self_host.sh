#!/usr/bin/env bash

source "$(dirname "$0")/_common.sh"

case "${1:-}" in
  validate)
    if [ "${GITHUB_REF_TYPE:-}" != branch ]; then
      echo "Self-host deployment must be dispatched from a branch" >&2
      exit 1
    fi
    for name in JWT_SECRET NEON_API_KEY NEON_PROJECT_ID RENDER_API_KEY \
      RENDER_OWNER_ID RENDER_SERVICE_PREFIX; do require_env "$name"; done
    [[ "$RENDER_SERVICE_PREFIX" =~ ^[a-z0-9][a-z0-9-]{1,38}[a-z0-9]$ ]]
    ;;
  resolve-neon)
    for name in NEON_API_KEY NEON_PROJECT_ID; do require_env "$name"; done
    cli=(npx --yes neonctl@2.36.0)
    branches_json="$("${cli[@]}" branches list --project-id "$NEON_PROJECT_ID" \
      --output json --no-analytics --no-color)"
    matches="$(jq -c '[.[] | select(.default == true)]' <<<"$branches_json")"
    test "$(jq 'length' <<<"$matches")" = 1
    branch_id="$(jq -r '.[0].id' <<<"$matches")"
    source_database_url="$("${cli[@]}" connection-string "$branch_id" \
      --project-id "$NEON_PROJECT_ID" --role-name neondb_owner \
      --database-name neondb --pooled --no-color)"
    migration_database_url="$("${cli[@]}" connection-string "$branch_id" \
      --project-id "$NEON_PROJECT_ID" --role-name neondb_owner \
      --database-name neondb --no-pooled --no-color)"
    mask_value "$source_database_url"
    mask_value "$migration_database_url"
    emit_output source_database_url "$source_database_url"
    emit_output migration_database_url "$migration_database_url"
    ;;
  summarize)
    require_env RESULT_FILE
    test "$(jq -r '.status' "$RESULT_FILE")" = ok
    append_summary <<EOF
### Self-hosted InKCre on Render + Neon

- Commit: \`$(jq -r '.commit' "$RESULT_FILE")\`
- Core service: \`$(jq -r '.core_service' "$RESULT_FILE")\`
- Core URL: $(jq -r '.core_url' "$RESULT_FILE")
- PostgREST service: \`$(jq -r '.postgrest_service' "$RESULT_FILE")\`
- PostgREST URL: $(jq -r '.postgrest_url' "$RESULT_FILE")
- Peer ID: \`$(jq -r '.peer_id' "$RESULT_FILE")\`
- Admission: private JWT secret from this repository
EOF
    ;;
  *) echo "usage: $0 validate|resolve-neon|summarize" >&2; exit 2 ;;
esac
