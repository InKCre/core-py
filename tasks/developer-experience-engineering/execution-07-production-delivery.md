# Execution 07 — Main-To-Production Delivery

## MVT Core

- Objective & Hypothesis: turn a green `main` commit into one immutable OCI release on a
  new Heroku production app backed by a canonical Neon `production` branch copied from the
  durable checkpoint, while preserving the legacy staging runtime and both recovery paths.
  The hypothesis is that a trusted post-CI workflow, separate pooled/runtime and
  direct/migration connections, and an application-only rollback make production delivery
  repeatable without making Heroku the platform contract.
- Guardrails Touched: `main` is the only production source; the exact CI-proven SHA is
  built without deployment secrets; one release process applies checked-in migrations;
  production data comes from the checkpoint rather than seed; no automatic database
  downgrade; no force-push/reset of divergent Git history; no custom-domain cutover in this
  execution.
- Verification: prove the production branch against the recovered manifest and canonical
  migration head, require `main` plus green repository/artifact checks, deploy both process
  images, inspect release logs, require liveness/readiness and exact head, then demonstrate
  application-release rollback without changing the database head.

## Classification And Mode

- Constraint:
  - Git `main` is the production policy branch;
  - Heroku remains the current compute provider but must be replaceable;
  - Neon remains the database provider;
  - checked-in extensions are the immutable built-in image profile.
- Reality:
  - `main` has seven unique Cloudflare experiment/revert commits but its tree equals the
    `main`/`develop` merge-base;
  - `develop` has 131 unique commits before this delivery work;
  - GitHub `production` exists without secrets, variables, branch policy, or reviewers;
  - no Heroku production app and no Neon `production` branch exist;
  - the only data-bearing runtime is legacy `inkcre-core-staging` → Neon `staging`;
  - the Neon plan cannot protect branches.
- Artifact: production workflow/actions, environment/branch protections, canonical Neon
  branch, Heroku production app, deployment and rollback evidence, and main reconciliation
  PR.
- Active mode: Execute for isolated provisioning and automation, then Solidify before Git
  merge and deployment; re-enter Diagnose on any release, data, or probe mismatch.

## Impact Handshake

- Targets:
  - GitHub environment `production`, `main` protection, and production workflow;
  - Neon branch `production`, parented to checkpoint `br-polished-forest-a1m6qwrd`;
  - Heroku app `inkcre-core-production`, pipeline `inkcre-core`, stage `production`;
  - a history-preserving delivery-line merge into `main`.
- Current state:
  - encrypted archive and checkpoint recovery are verified;
  - convergence head `c4e8a7b6d5f0` is proven against both the legacy production-copy and a
    fresh PostgreSQL database;
  - PR preview image/release/probe delivery is green;
  - legacy staging remains failed/stale but contains the preserved source dataset.
- Requested operation:
  - add an optional `MIGRATION_DATABASE_URL` which falls back to `DATABASE_URL`;
  - configure preview and production release processes with a direct Neon connection while
    web processes keep the pooled connection;
  - create a main-SHA verification action and production delivery action;
  - create a serialized workflow triggered only after the repository/artifact workflow
    succeeds for `main`, with a manually recoverable main-only path;
  - create a dedicated one-year Heroku authorization and store it only in the production
    environment alongside production runtime secrets;
  - create and verify the canonical production database copy, then apply only the checked-in
    convergence revision;
  - create/verify the production Heroku app with container stack, no addons, one Eco web
    process, deterministic client identity, and explicit configuration;
  - merge the prepared delivery line into `main` through reviewed Git history and run the
    production workflow for that exact SHA;
  - record release, health, schema, and rollback evidence.
- Explicit exclusions:
  - no write, migration, rename, config change, scale change, or deletion on Neon `staging`
    or Heroku `inkcre-core-staging`;
  - no deletion or mutation of the durable checkpoint or encrypted archive;
  - no production rows reconstructed from seed;
  - no force-push, rebase, reset, or history rewrite of `main`;
  - no custom domain, DNS, external traffic switch, staging app destruction, or checkpoint
    deletion;
  - no Heroku PostgreSQL addon;
  - no database downgrade as part of application rollback;
  - no touch to `docs/_shared/**` or `portless.json`.
- Invariants:
  - production branch/app names and provider IDs are resolved before each mutation;
  - GitHub environment branch policy admits only `main`;
  - deployment secrets enter scope only after the source SHA passes checks and images build;
  - runtime and migration URLs resolve to the exact same production branch but use pooled
    and direct endpoints respectively;
  - the production release image can only run `alembic upgrade head`;
  - pre/post database manifests keep the same table set and row counts;
  - one web dyno remains the scheduler owner;
  - a failed probe rolls back only to the previous Heroku release, and the workflow remains
    failed for operator attention.
- Likely files:
  - `migrations/settings.py`, `.env.example`, migration settings tests;
  - preview delivery configuration for the split URL contract;
  - `.github/actions/production-verify/action.yml`;
  - `.github/actions/production-delivery/action.yml`;
  - `.github/workflows/production-deploy.yml`;
  - workflow lint/pre-commit inputs if needed;
  - `docs/40-deployment/heroku.md`, `docs/40-deployment/neon.md`, and this packet.

## Target Sequence

```mermaid
sequenceDiagram
  participant Main as main SHA
  participant CI as Repository/artifact CI
  participant CD as Trusted production workflow
  participant Neon as Neon production branch
  participant Registry as Heroku Registry
  participant Release as Heroku release process
  participant Web as Heroku web process

  Main->>CI: push after reviewed merge
  CI->>CI: repository + fresh DB + OCI probes
  CI-->>CD: successful workflow_run for exact SHA
  CD->>CD: verify main ref and required checks
  CD->>Registry: build without secrets, then push web/release
  CD->>Neon: resolve direct + pooled URLs for production
  CD->>Release: release both images
  Release->>Neon: alembic upgrade head via direct URL
  Release-->>CD: successful release logs
  CD->>Web: scale one Eco dyno
  CD->>Web: probe /livez and /readyz
  Web->>Neon: readiness via pooled URL
  alt probe fails
    CD->>Registry: roll back previous app release
    CD-->>Main: fail deployment for operator attention
  end
```

## Acceptance Criteria

1. `MIGRATION_DATABASE_URL` is optional, migration-only, normalized like
   `DATABASE_URL`, and falls back without affecting existing environments.
2. Production verification accepts only the current `main` SHA with successful hermetic
   repository and portable artifact/fresh database checks.
3. GitHub `production` stores masked deployment/runtime secrets and admits only `main`;
   main rejects unreviewed/unverified direct delivery.
4. Neon `production` is a no-TTL child of the exact checkpoint; before migration its
   manifest matches the preserved source, and afterward only the Alembic head changes.
5. `inkcre-core-production` is a US container app in pipeline production stage, has no
   addons, and receives no database from Heroku.
6. Docker builds receive no deployment secrets; web and release images derive from the
   same exact main SHA.
7. Release migration succeeds to `c4e8a7b6d5f0`; `/livez` and `/readyz` return 200 from
   the default production URL with one Eco web dyno.
8. Application rollback is demonstrated without changing the production database head or
   row counts.
9. Legacy staging app/database, durable checkpoint, encrypted archive, and production rows
   remain unchanged.
10. Full local checks, actionlint, and GitHub repository/artifact checks pass.

## Cutover And Follow-Up Boundary

This execution establishes a verified production endpoint but does not move custom-domain
or DNS traffic. After PR close removes its preview resources, `preview-base` should be
recreated from the canonical production branch and sanitized under its existing exact-name
guard; until then it remains a data-free, migrated baseline with the same schema head.

Later cleanup may archive the legacy staging app/branch only after an explicit retention
window and independent confirmation that no consumer uses them. The checkpoint and
encrypted archive have a separate retention decision and are not cleanup candidates here.
