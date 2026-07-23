# Heroku

## Artifact And Process Model

Heroku consumes the same provider-neutral OCI source proved in CI. The `Dockerfile` exposes
two final targets:

- `web`: starts the application server
- `release`: applies `alembic upgrade head` and has no web command

The workflow pushes both targets to Heroku Container Registry and releases `web` and
`release` together. Heroku therefore supplies compute, configuration, and routing; it is not
the build-system contract and owns no database.

Heroku appends process commands to the image entry point as
`/bin/sh -c <process-command>`. `scripts/container.py` recognizes that exact adapter shape
only when `<process-command>` is one of its built-in commands; it never evaluates an
arbitrary shell expression.

`Procfile`, `requirements.txt`, and `app.json` remain legacy buildpack entry points for the
existing staging app. They do not govern container previews and must not be used as the
production CD contract without a separate cutover.

## Pull Request Previews

Trusted same-repository pull requests use:

- app name `inkcre-core-pr-<number>`
- pipeline `inkcre-core`, stage `review`
- container stack in the US region
- one Eco `web` dyno
- matching Neon branch `preview/pr-<number>`
- no Heroku PostgreSQL or other addon

`.github/actions/preview-verify/action.yml` verifies that the exact PR head passed the
repository, portable-artifact, and preview-database checks. The caller then builds both
images in a step that receives no deployment inputs. Only afterward does
`.github/actions/preview-delivery/action.yml` resolve the masked Neon URL, configure the
app, push both process images, run the release, and probe `/livez` plus `/readyz`.

`.github/workflows/preview-deploy.yml` invokes that action from a trusted post-CI
`workflow_run`. The verify and delivery implementations are checked out from
`github.workflow_sha`;
untrusted PR source is checked out separately and is only used as the Docker build context.
A PR-close event destroys only the deterministic app. The matching Neon workflow
independently deletes only its deterministic database branch.

The manual `workflow_dispatch` input on `.github/workflows/ci.yml` is a recovery and initial
bootstrap path. It executes the same repository and artifact checks before calling the same
delivery action.

## Secret Boundary

The GitHub `preview` environment owns `HEROKU_API_KEY`, `LLM_SP_AK`, and
`LLM_SP_BASE_URL`. `NEON_API_KEY` remains a repository secret and `NEON_PROJECT_ID` a
repository variable. Deployment values are never Docker build arguments or persisted in an
artifact.

Heroku configuration is explicit. `DATABASE_SCALE_0=true` enables resilient Neon
connections, observability uses the non-database backend, and the fixed checked-in extension
profile boots normally. `CLIENT_ID` is deterministic per PR so restarts do not create a new
runtime identity.

## Migration And Rollback Constraint

The release target is a single-writer `alembic upgrade head` operation. A failed migration
fails the release; rolling the web image back does not reverse the database. Every revision
must therefore pass the fresh pgvector artifact check and the matching Neon preview before
delivery.

Production needs its own GitHub environment, data backup and restore rehearsal, canonical
Neon branch decision, and rollback evidence. Preview automation is not authority to mutate
the existing staging app or production data.
