#!/usr/bin/env bash

source "$(dirname "$0")/_common.sh"

require_env GH_TOKEN

if git diff --quiet; then
  echo "No pending release fragments."
  exit 0
fi

git config user.name github-actions[bot]
git config user.email 41898282+github-actions[bot]@users.noreply.github.com
git switch --create release/next
git add --all
git commit -m "chore(release): prepare next projects"
git push --force origin HEAD:release/next
if [ "$(gh pr list --head release/next --state open --json number --jq length)" = 0 ]; then
  gh pr create \
    --base main \
    --head release/next \
    --title "chore(release): prepare next projects" \
    --body "Generated from checked protected main. This pull request prepares versions and changelogs; it publishes nothing."
fi
