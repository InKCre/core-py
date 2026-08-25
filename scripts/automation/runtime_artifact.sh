#!/usr/bin/env bash

source "$(dirname "$0")/_common.sh"

case "${1:-}" in
  verify-main-source)
    require_env HEAD_SHA
    test "$(git rev-parse HEAD)" = "$HEAD_SHA"
    git fetch --no-tags origin main
    test "$(git rev-parse origin/main)" = "$HEAD_SHA"
    ;;
  verify-schema-evidence)
    require_env HEAD_SHA
    python3 scripts/package_database_schema.py \
      --schema release/database-contract/database-schema.sql \
      --roles release/database-contract/database-roles.sql \
      --runtime-contract release/database-contract/runtime-contract.json \
      --output "${RUNNER_TEMP:-/tmp}/manifest.json" \
      --source-revision "$HEAD_SHA"
    cmp "${RUNNER_TEMP:-/tmp}/manifest.json" release/database-contract/manifest.json
    ;;
  publish-immutable)
    require_env GHCR_TOKEN
    require_env HEAD_SHA
    require_env GITHUB_REPOSITORY
    require_env GITHUB_ACTOR
    repository="${GITHUB_REPOSITORY,,}"
    image="ghcr.io/$repository"
    commit_ref="$image:$HEAD_SHA"
    docker build --platform linux/amd64 --provenance=false \
      --build-arg "SOURCE_REVISION=$HEAD_SHA" --target service \
      --tag "$commit_ref" .
    test "$(docker inspect --format='{{json .Config.Entrypoint}}' "$commit_ref")" = null
    docker inspect --format='{{json .Config.Cmd}}' "$commit_ref" |
      jq -e '. == ["python", "scripts/container.py", "web"]' >/dev/null
    docker run --rm "$commit_ref" python scripts/container.py db schema --json >/dev/null
    test "$(docker inspect --format='{{.Config.User}}' "$commit_ref")" = inkcre
    docker run --rm "$commit_ref" python -c \
      'import pathlib, pip; assert not pathlib.Path("/app/extensions").exists()'
    printf '%s' "$GHCR_TOKEN" |
      docker login ghcr.io --username "$GITHUB_ACTOR" --password-stdin
    docker push "$commit_ref"
    docker pull "$commit_ref" >/dev/null
    digest_ref="$(docker inspect --format='{{index .RepoDigests 0}}' "$commit_ref")"
    test "${digest_ref%%@*}" = "$image"
    emit_output commit_ref "$commit_ref"
    emit_output digest_ref "$digest_ref"
    emit_output image "$image"
    ;;
  promote-main)
    for name in COMMIT_REF DIGEST_REF IMAGE; do require_env "$name"; done
    docker tag "$COMMIT_REF" "$IMAGE:main"
    docker push "$IMAGE:main"
    docker pull "$IMAGE:main" >/dev/null
    docker inspect --format='{{range .RepoDigests}}{{println .}}{{end}}' "$IMAGE:main" |
      grep --fixed-strings --line-regexp "$DIGEST_REF"
    ;;
  summarize-runtime)
    for name in HEAD_SHA IMAGE_DIGEST MAIN_PROMOTION; do require_env "$name"; done
    append_summary <<EOF
### core-py runtime

- Delivery source revision: \`$HEAD_SHA\`
- Immutable image: \`$IMAGE_DIGEST\`
- Mutable main promotion: \`$MAIN_PROMOTION\`
- Contract command: \`python scripts/container.py db contract --json\`
- Schema command: \`python scripts/container.py db schema --json\`
EOF
    ;;
  resolve-production-source)
    head_sha="${EVENT_HEAD_SHA:-${DISPATCH_HEAD_SHA:-}}"
    require_env head_sha
    emit_output head_sha "$head_sha"
    ;;
  pull-production)
    for name in GHCR_TOKEN HEAD_SHA GITHUB_REPOSITORY GITHUB_ACTOR; do require_env "$name"; done
    image="ghcr.io/${GITHUB_REPOSITORY,,}"
    commit_ref="$image:$HEAD_SHA"
    printf '%s' "$GHCR_TOKEN" |
      docker login ghcr.io --username "$GITHUB_ACTOR" --password-stdin
    docker pull "$commit_ref"
    test "$(docker inspect --format='{{index .Config.Labels "org.opencontainers.image.revision"}}' "$commit_ref")" = "$HEAD_SHA"
    docker run --rm "$commit_ref" python scripts/container.py db schema --json >/dev/null
    digest_ref="$(docker inspect --format='{{index .RepoDigests 0}}' "$commit_ref")"
    test "${digest_ref%%@*}" = "$image"
    docker tag "$digest_ref" "inkcre-production-web:$HEAD_SHA"
    emit_output digest_ref "$digest_ref"
    ;;
  build-production-transports)
    require_env HEAD_SHA
    docker build --platform linux/amd64 --provenance=false \
      --build-arg "SOURCE_REVISION=$HEAD_SHA" --target heroku-release \
      --tag "inkcre-production-release:$HEAD_SHA" .
    docker build --platform linux/amd64 --provenance=false \
      --build-arg "SOURCE_REVISION=$HEAD_SHA" --file Dockerfile.postgrest \
      --tag "inkcre-production-postgrest:$HEAD_SHA" .
    ;;
  promote-stable)
    for name in GHCR_TOKEN HEAD_SHA IMMUTABLE_CORE_IMAGE GITHUB_REPOSITORY GITHUB_ACTOR; do
      require_env "$name"
    done
    image="ghcr.io/${GITHUB_REPOSITORY,,}"
    printf '%s' "$GHCR_TOKEN" |
      docker login ghcr.io --username "$GITHUB_ACTOR" --password-stdin
    docker tag "$IMMUTABLE_CORE_IMAGE" "$image:stable"
    docker push "$image:stable"
    append_summary <<EOF
### Production-admitted core service

- Commit: \`$HEAD_SHA\`
- Immutable GHCR image: \`$IMMUTABLE_CORE_IMAGE\`
- Discovery channel: \`$image:stable\`
EOF
    ;;
  *)
    echo "unknown runtime artifact command: ${1:-}" >&2
    exit 2
    ;;
esac
