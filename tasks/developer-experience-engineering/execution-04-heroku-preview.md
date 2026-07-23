# Execution 04 — Heroku Preview Delivery

## MVT Core

- Objective & Hypothesis: deploy the already-proven OCI source as deterministic Heroku
  `web` and `release` process images for each trusted PR, configure it with the matching
  Neon `preview/pr-<number>` URL, verify readiness, and destroy only that app on PR close.
  The hypothesis is that a trusted post-CI workflow makes previews automatic without giving
  account-wide Heroku credentials to PR-controlled workflow definitions or Docker builds.
- Guardrails Touched: Heroku/LLM credentials are GitHub `preview` environment secrets;
  builds receive no deployment secrets; release only runs `alembic upgrade head`; preview
  has one web dyno because it owns APScheduler; no Heroku Postgres addon is provisioned.
- Verification: manually bootstrap PR 17 from the trusted workflow, inspect app/pipeline
  state without printing config values, verify release success plus `/livez` and `/readyz`,
  then prove the future workflow-run and close-cleanup event contracts statically.

## Classification And Mode

- Constraint: local Docker is unavailable, so Heroku Registry publishing must run on a
  GitHub runner after artifact CI. New reusable workflows cannot be bootstrapped reliably
  from a non-default branch, so verification and delivery are local composite actions with
  a separate secret-free Docker build step between them.
- Reality: the only current app is `inkcre-core-staging` on the Python buildpack; pipeline
  `inkcre-core` has no production or review app. GitHub has no Heroku deploy credential.
- Reality: Heroku wraps the release process command in an internal shell program for log
  streaming. Appending that program to the provider-neutral entry point is incompatible
  with its strict one-command parser.
- Artifact: Heroku-compatible image targets, trusted preview deploy/cleanup workflow,
  preview environment secret boundary, one live PR-17 preview, and a persistent workflow
  syntax contract for agent-authored automation.
- Active mode: Execute, with Diagnose on provider failures.

## Impact Handshake

- Target:
  - `Dockerfile` process targets and a new trusted deployment workflow;
  - GitHub environment `preview` and its deployment secrets;
  - Heroku app `inkcre-core-pr-17` in pipeline `inkcre-core` review stage;
  - matching Neon branch `preview/pr-17`.
- Current state:
  - OCI build, fresh migration, metadata check, web startup, liveness, and readiness are
    green in CI;
  - Neon preview lifecycle is green and contains no production rows;
  - production cutover has not begun.
- Requested operation:
  - add separate `heroku-web` and `heroku-release` targets from the same runtime stage;
  - adapt Heroku through target metadata while keeping the application parser strict;
  - accept automatic `workflow_run` only after repository/artifact CI succeeds;
  - retain manual dispatch for controlled bootstrap and recovery;
  - build before deployment secrets enter scope, then push both process images;
  - create/reuse deterministic app, attach to review stage, set explicit runtime config,
    release, scale to one web dyno, and probe;
  - destroy the exact app on trusted PR-close events.
  - load the automatic delivery implementation from the trusted workflow SHA while using
    the isolated PR checkout only as a Docker build context.
- Explicit exclusions:
  - no mutation of `inkcre-core-staging`;
  - no `main`/production deployment, production app creation, or traffic switch;
  - no production database dump/restore/reset;
  - no dynamic extension installation and no Heroku PostgreSQL addon;
  - no merge or ready-for-review transition.
- Invariants:
  - Heroku API token and LLM credential values never appear in logs or Git;
  - untrusted build steps do not receive deployment secrets;
  - database URL always resolves from the deterministic Neon preview branch;
  - release image can only execute the checked-in migrate command;
  - app and database cleanup use the same PR number;
  - web formation remains exactly one until scheduler ownership is extracted;
  - `portless.json` remains untouched.
- Likely files: `Dockerfile`, `.github/workflows/ci.yml`,
  `.github/actions/preview-verify/action.yml`, `.github/actions/preview-delivery/action.yml`,
  `.github/workflows/preview-deploy.yml`,
  `.github/workflows/copilot-setup-steps.yml`, `.github/workflows/openapi-doc.yml`,
  `.pre-commit-config.yaml`, `docs/40-deployment/heroku.md`, and this packet.

## Acceptance Criteria

1. GitHub `preview` environment holds masked Heroku and LLM inputs; no value is printed.
2. The workflow resolves a same-repository PR and requires successful repository, artifact,
   and preview-database checks for the same head SHA.
3. Docker build has no deployment secrets; registry login begins only after build.
4. `inkcre-core-pr-17` uses container stack, pipeline review stage, and no addons.
5. Release process applies `upgrade head`; web process starts from the same source image.
6. The app has one web dyno, `/livez` returns 200, and `/readyz` returns 200.
7. PR close cleanup can only target `inkcre-core-pr-<number>`.
8. `actionlint` is a checked-in pre-commit contract and all workflows pass it.
9. Existing staging app, staging config, and production data remain unchanged.

## Follow-Up Boundary

Production delivery will reuse the process-image contract but requires a separate production
environment, backup artifact, restore rehearsal, canonical Neon branch decision, `main`
reconciliation, and explicit cutover/rollback evidence.
