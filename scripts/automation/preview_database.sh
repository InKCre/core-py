#!/usr/bin/env bash

source "$(dirname "$0")/_common.sh"

case "${1:-}" in
  expiration)
    expires_at="$(
      python3 -c 'from datetime import UTC, datetime, timedelta; print((datetime.now(UTC) + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"))'
    )"
    emit_output expires_at "$expires_at"
    ;;
  summarize)
    for name in NEON_BRANCH_NAME NEON_PARENT_BRANCH; do require_env "$name"; done
    append_summary <<EOF
### Neon preview branch

- Name: \`$NEON_BRANCH_NAME\`
- Parent: \`$NEON_PARENT_BRANCH\`
- Lifecycle owner: preview delivery
EOF
    ;;
  cleanup)
    for name in NEON_API_KEY NEON_PROJECT_ID NEON_BRANCH_NAME NEON_PARENT_BRANCH; do
      require_env "$name"
    done
    if [[ ! "$NEON_BRANCH_NAME" =~ ^preview/core-py/pr-[0-9]+$ ]]; then
      echo "Unexpected preview branch namespace: $NEON_BRANCH_NAME" >&2
      exit 1
    fi
    cli=(npx --yes neonctl@2.36.0)
    list_json="$("${cli[@]}" branches list --project-id "$NEON_PROJECT_ID" \
      --output json --no-analytics --no-color)"
    parent_matches="$(jq -c --arg name "$NEON_PARENT_BRANCH" \
      '[.[] | select(.name == $name)]' <<<"$list_json")"
    test "$(jq 'length' <<<"$parent_matches")" = 1
    expected_parent_id="$(jq -r '.[0].id' <<<"$parent_matches")"
    [[ "$expected_parent_id" =~ ^br-[a-z0-9-]+$ ]]
    matches="$(jq -c --arg name "$NEON_BRANCH_NAME" \
      '[.[] | select(.name == $name)]' <<<"$list_json")"
    match_count="$(jq 'length' <<<"$matches")"
    if [ "$match_count" = 0 ]; then
      echo "Neon branch already absent: $NEON_BRANCH_NAME"
      exit 0
    fi
    test "$match_count" = 1
    branch_id="$(jq -r '.[0].id' <<<"$matches")"
    [[ "$branch_id" =~ ^br-[a-z0-9-]+$ ]]
    test "$(jq -r '.[0].parent_id' <<<"$matches")" = "$expected_parent_id"
    "${cli[@]}" branches delete "$branch_id" --project-id "$NEON_PROJECT_ID" \
      --no-analytics --no-color
    ;;
  *) echo "usage: $0 expiration|summarize|cleanup" >&2; exit 2 ;;
esac
