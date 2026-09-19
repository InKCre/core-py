#!/usr/bin/env bash

source "$(dirname "$0")/_common.sh"

case "${1:-}" in
  verify-main-source)
    require_env HEAD_SHA
    test "$(git rev-parse HEAD)" = "$HEAD_SHA"
    git fetch --no-tags origin main
    test "$(git rev-parse origin/main)" = "$HEAD_SHA"
    ;;
  build-schema-source)
    for name in HEAD_SHA IMAGE_TAG; do require_env "$name"; done
    docker build --platform linux/amd64 --provenance=false \
      --build-arg "SOURCE_REVISION=$HEAD_SHA" --target runtime \
      --tag "$IMAGE_TAG" .
    ;;
  stage-schema-evidence)
    require_env HEAD_SHA
    contract_directory="${RUNNER_TEMP:-/tmp}/database-contract"
    for file in database-schema.sql database-roles.sql runtime-contract.json manifest.json; do
      test -f "$contract_directory/$file"
    done
    python3 scripts/package_database_schema.py \
      --schema "$contract_directory/database-schema.sql" \
      --roles "$contract_directory/database-roles.sql" \
      --runtime-contract "$contract_directory/runtime-contract.json" \
      --output "${RUNNER_TEMP:-/tmp}/manifest.json" \
      --source-revision "$HEAD_SHA"
    cmp "${RUNNER_TEMP:-/tmp}/manifest.json" "$contract_directory/manifest.json"
    install --mode 0644 "$contract_directory"/*.sql "$contract_directory"/*.json \
      release/database-contract/
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
  summarize-production)
    for name in HEAD_SHA EVENT_NAME JOB_STATUS SELECTION_RESULT DELIVERY_RESULT STABLE_RESULT; do
      require_env "$name"
    done
    core_version="$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')"
    if [ "$SELECTION_RESULT" = success ] && [ "${SELECTED:-}" = false ]; then
      result="未部署：Core 版本未变，本次为空操作；未修改 stable。"
    elif [ "$DELIVERY_RESULT" = success ] && [ "$STABLE_RESULT" = success ]; then
      result="生产发布完成：部署及线上探测通过，stable 已更新。"
    else
      result="生产发布未完成；可能已有部分部署效果，请查看失败或取消步骤，不能据此声称生产未变。"
    fi
    append_summary <<EOF
### Core 生产发布结果

$result

| 项目 | 结果 |
| --- | --- |
| 源码声明的 Core 版本 | \`$core_version\` |
| 源码提交 | \`$HEAD_SHA\` |
| 触发方式 | \`$EVENT_NAME\`（workflow_dispatch 为手动恢复） |
| Job 状态 | \`$JOB_STATUS\` |
| 发布选择 | \`$SELECTION_RESULT\` / selected=\`${SELECTED:-未取得}\` |
| 候选不可变镜像 | \`${IMAGE_DIGEST:-未取得}\` |
| 部署及线上探测 | \`$DELIVERY_RESULT\` |
| stable 更新 | \`$STABLE_RESULT\` |

源码版本不等同于当前线上版本。只有部署探测与 stable 更新均成功才表示本次发布完成。
EOF
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
