# Heroku

## Artifact And Process Model

Heroku consumes the same provider-neutral OCI source proved in CI. The `Dockerfile` exposes
two provider-adapted targets:

- `heroku-web`: starts the application server
- `heroku-release`: applies `alembic upgrade head` and has no web command

The workflow pushes both targets to Heroku Container Registry and releases `web` and
`release` together. Heroku therefore supplies compute, configuration, and routing; it is not
the build-system contract and owns no database.

Heroku wraps release commands in an internal shell program to stream release logs. These
two targets therefore clear the provider-neutral image entry point and put the complete
allowlisted Python invocation in `CMD`. `scripts/container.py` remains strict and never
parses or evaluates Heroku's shell wrapper. They include `curl` solely so release output is
streamed back to the deployment job rather than requiring a later app-log lookup.

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

## Production Delivery

Production uses:

- Git source: the exact current `main` SHA
- app: `inkcre-core-production`
- pipeline: `inkcre-core`, stage `production`
- stack/region: container, US
- database: canonical Neon branch `production`
- formation: one Eco `web` process and one on-demand `release` process
- addons: none

`.github/workflows/production-deploy.yml` runs only after the repository/artifact workflow
succeeds for a `main` push, or through a main-only recovery dispatch. The verifier resolves
the current main ref and requires the hermetic repository and fresh-database artifact checks
for the same SHA. Images are built before any deployment input is referenced.

The delivery action guards the exact production branch ID and checkpoint parent, resolves a
pooled `DATABASE_URL` for web traffic and a direct `MIGRATION_DATABASE_URL` for Alembic,
then releases both Heroku process images. A failed post-release probe rolls the application
back to its previous deployed release when one exists, but still fails the workflow.
Application rollback never runs an Alembic downgrade.

For a new app, explicit config is installed before its first image release. For an existing
app, delivery first proves that its current pooled and direct hosts still belong to the
expected Neon branch, releases the new image against that same database, and only then
updates config. This prevents a Heroku config release from running a new schema through an
older migration image. Every image and config release is polled to a terminal successful
state. Only registry login and image transfer receive bounded retries; migration and probe
failures remain operator-visible failures.

The default Heroku URL is the initial verification endpoint. Custom-domain and DNS traffic
cutover are separate decisions; the legacy staging app remains unchanged during bootstrap.

## Secret Boundary

The GitHub `preview` environment owns `HEROKU_API_KEY`, `LLM_SP_AK`, and
`LLM_SP_BASE_URL`. `NEON_API_KEY` remains a repository secret and `NEON_PROJECT_ID` a
repository variable. Deployment values are never Docker build arguments or persisted in an
artifact.

The Heroku secret is a dedicated global authorization named
`GitHub InKCre/core-py preview CD`, created with a 365-day lifetime on 2026-07-23. Rotate it
no later than 2027-07-23 and revoke the superseded authorization after a green preview
deployment.

The GitHub `production` environment independently owns its Heroku authorization, JWT
signing secret, and LLM inputs. It also records exact non-secret app and Neon branch
identities and admits deployments from `main` only. Production must not reuse the preview
Heroku authorization or JWT secret.

Heroku configuration is explicit. `DATABASE_SCALE_0=true` enables resilient Neon
connections, `OBSRV__LOGGING_BACKEND=none` keeps console logs without a remote/database
handler, and the fixed checked-in extension profile boots normally. `CLIENT_ID` is
deterministic per app so restarts do not create a new runtime identity.

## Migration And Rollback Constraint

The release target is a single-writer `alembic upgrade head` operation. A failed migration
fails the release; rolling the web image back does not reverse the database. Every revision
must therefore pass the fresh pgvector artifact check and the matching Neon preview before
delivery.

Preview automation is not authority to mutate the existing staging app or production data.
