# Legacy Runtime And Consumer Audit

Audit date: 2026-07-24

## Scope And Method

- Read-only source, Git, GitHub, Heroku, Neon, and database catalog inspection.
- No secret values are recorded in this artifact.
- No durable App, branch, database, role, credential, webhook, addon, deployment, or browser
  configuration was mutated. HTTP probes transiently woke the legacy PostgREST Eco dyno and
  performed one authenticated read.
- Browser localStorage and WebExtension storage are intentionally origin/profile-local and
  cannot be centrally enumerated. Absence from repository or provider state is not proof that
  no local browser still stores a legacy URL.

## Executive Findings

1. No active source or durable deployment document outside task history hard-codes the legacy
   staging core hostname, legacy PostgREST hostname, or staging Neon endpoint.
2. Canonical production has no PostgREST. The only PostgREST is a legacy Heroku app connected
   to the old staging Neon branch.
3. The legacy `anonymous` database role is critically misprovisioned in both staging and
   production: it is a LOGIN role with `CREATEDB`, `CREATEROLE`, and membership in
   `neon_superuser`.
4. Both databases lack `authenticator` and authenticated default ACLs. Existing authenticated
   table privileges are incomplete for client-web's real write paths.
5. The current Heroku topology already uses one pipeline and Eco dynos. The durable staging app
   is stale and crashed; the old PostgREST is outside the pipeline.
6. GitHub and Neon still retain stale staging/develop control-plane resources.
7. client-web has no current CI/CD or Cloudflare Pages deployment contract. Its only recorded
   deployment is an inactive 2025 Heroku deployment.
8. client-web runtime configuration is browser-local and defaults to unconfigured values.
   Canonical production discovery and legacy-URL migration do not yet exist.

## Source And Repository Evidence

### core-py

- `main` is two commits ahead of `develop`; `develop` has no unique commits.
- The only open PR targets `main`.
- remote `staging` is a stale 2025 lineage.
- CI still names both `develop` and `main`.
- preview workflows currently accept internal PRs without a base-branch allowlist.
- active source contains no legacy staging/PostgREST URL.
- the current core worktree is `codex/pyrefly-gate`; the unrelated untracked
  `portless.json` remains untouched.

### client-web

- remote `develop` is 144 commits ahead of remote `main`; neither branch is protected.
- there are no open PRs.
- the local client-web worktree contains extensive uncommitted DX/static-runtime work and must
  be preserved as a separate ownership surface before this task mutates that repo.
- the only checked-in workflow is the obsolete Copilot setup workflow.
- there is no checked-in Pages CD, database runtime, PostgREST lifecycle, or E2E workflow.
- local/browser config is stored under one adapter-owned key in localStorage; webext uses its
  own extension storage adapter.
- config import/export excludes the JWT secret, but no deployment profile supplies canonical
  non-secret defaults and no validator recognizes retired endpoints.

## Heroku Evidence

### Pipeline

One pipeline, `inkcre-core`, currently contains:

| App | Stage | Stack | Formation |
|---|---|---|---|
| `inkcre-core-production` | production | container | one Eco web dyno |
| `inkcre-core-staging` | staging | Heroku Python buildpack | one crashed Eco web dyno |
| `inkcre-core-pr-31` | review | container | one Eco web dyno |

`inkcre-pgrst` is outside the pipeline.

### Legacy staging

- only the default Heroku domain exists; there is no custom domain.
- the app is crashed and its last release failed in December 2025.
- it owns a Logtail addon and Better Stack log drain.
- retained router logs show no July traffic, but Heroku log retention is not a durable
  consumer ledger.

### Legacy PostgREST

- default Heroku domain only; no addon or log drain.
- Eco web dyno.
- PostgREST `10.0.0`, `public` schema, `anonymous` configured, no JWT audience.
- connects as provider-specific `neondb_owner`.
- JWT secret matches legacy staging core but not production core.
- after wake, authenticated `clients` read returns HTTP 200 and anonymous access returns 401.
- retained pre-audit router logs contain no earlier request evidence; this is weak negative
  evidence, not proof of zero browser consumers.

### Canonical production

- default Heroku domain only; no addon or log drain.
- one Eco web dyno.
- no `PGRST_*` configuration or PostgREST process.

## GitHub Evidence

- an active core-py webhook sends every repository event to Heroku's
  `kolkrabbi.heroku.com` integration endpoint.
- the obsolete `inkcre-core-staging` GitHub environment still exists but contains no secrets
  or variables.
- production and preview environments contain the current protected delivery inputs.
- GitHub still lists an old OpenAPI workflow registration even though its workflow file is
  absent from the current worktree; it should be reconciled during control-plane cleanup.
- client-web's `inkcre-web` environment is empty.
- client-web has no repository variables, hooks, current Pages setup, or current active
  deployment. Its one recorded 2025 Heroku deployment is inactive.

## Neon Evidence

Current durable branches:

- `production`: canonical data-bearing production.
- `preview-base`: data-free child of production.
- `backup/pre-cutover-20260723`: durable recovery checkpoint; retain.
- `staging`: legacy data-bearing recovery source; retain until retirement gates pass.
- `develop`: stale child of staging; no durable purpose remains.
- `master`: provider default branch; reclassify separately rather than deleting casually.

Current disposable branch:

- `preview/pr-31`, with TTL.

The current bare `preview/pr-<number>` namespace will collide when multiple peer repositories
share the Neon project. Future identity must include repository plus PR number.

## Database Contract Evidence

Observed in both legacy staging and canonical production:

- no `authenticator` role;
- `authenticated` exists as NOLOGIN;
- `neondb_owner` has membership in `authenticated`, including duplicate grant records from
  different grantors/options;
- `anonymous` is LOGIN, `CREATEDB`, `CREATEROLE`, and a `neon_superuser` member;
- no authenticated default ACL;
- authenticated privileges:
  - write: `clients`, `extensions`, `sources`, and insert-only collection jobs;
  - read-only: `blocks`, `relations`, `logs`, storages, storage types, and source types.

This contradicts the confirmed policy that anonymous is denied and authenticated peers can
operate the complete protocol surface.

The staging database remains at `a1b2c3d4e5f6`; canonical production is at
`c4e8a7b6d5f0`.

Targeted scans of client URLs and configuration JSON found:

- no staging database row referencing either legacy Heroku app;
- one production client registration referencing canonical core production;
- no production row referencing a legacy staging/PostgREST hostname in the scanned client,
  extension, source, state, or storage configuration fields.

## Credential Incident During Audit

A legacy staging database connection credential was emitted transiently in a local command
error while normalizing its driver URL. It is not recorded in this task artifact, but the
credential must be rotated during P0 containment. Rotation must update or retire every
remaining staging consumer atomically and must not affect canonical production credentials.

## Disposable Execution Evidence

Two TTL-bound branches were created under the exact Neon project:

- a child of canonical production proved `c4e8a7b6d5f0 -> d9f4e2a1b7c3`, `public -> inkcre`,
  with every application-table row count preserved;
- a child of `preview-base` proved duplicate development init, duplicate seed, duplicate
  guarded reset, and one stable baseline fingerprint.

On the production-data copy:

- provider-created unsafe protocol roles were removed through the exact branch-scoped Neon
  control plane;
- portable SQL created final role attributes atomically;
- `authenticator` had no direct table access and could switch only to `authenticated`;
- `inkcre_core` connected as a native runtime peer and full JSON readiness passed without an
  owner URL;
- anonymous login was disabled;
- a preview-identity reset was refused without changing rows.

Neon permits SQL role creation but rejects general `ALTER ROLE` for non-provider owners.
The portable provisioner therefore creates final attributes atomically, treats a matching
existing role as a no-op, and fails closed on drift. Stable per-environment role passwords
are held by protected GitHub environments rather than regenerated per release.

## Retirement Gates

Before removing the old staging core/PostgREST or Neon staging branch:

1. contain the unsafe `anonymous` role on a disposable branch, then production/staging through
   a separately approved live-role runbook;
2. rotate the exposed legacy staging credential;
3. ship client-web legacy endpoint detection and a canonical production connection profile;
4. verify no current browser/webext config is deliberately retained through an explicit
   human migration window;
5. remove or re-home the all-events Heroku GitHub hook;
6. confirm the Logtail drain has no retention requirement;
7. retain the pre-cutover checkpoint and portable encrypted backup;
8. remove the stale GitHub staging environment and pipeline coupling;
9. archive/delete staging/develop resources in an order with bounded rollback evidence.

## Closure Evidence

All retirement gates were satisfied on 2026-07-24:

- canonical client-web production discovery, legacy-host detection, typed relation contract,
  local runtime, doctor, and isolated database E2E landed in PR #18;
- core preview PRs #37 and #38 proved repository-qualified Neon/Heroku creation and exact
  close cleanup;
- core production run `30091595400` passed after cleanup with both Eco peers ready;
- the Heroku pipeline's legacy GitHub repository link and its all-events hook are absent, so
  exact GitHub Actions controllers are the only review authority; the staging app, legacy
  PostgREST app, Logtail addon/drain, stale GitHub environments, and unused repository secrets
  are also absent; the historical OpenAPI workflow registration is disabled;
- core Git `develop` and `staging` are absent; client-web has only protected `main`, while the
  retired long-lived branches remain recoverable through archive tags;
- Neon `develop` is absent. The historical staging branch is storage-only under
  `archive/staging-lineage-20250824`; its endpoint is absent, and the branch itself is retained
  solely because it is an ancestor of the pre-cutover checkpoint and canonical production;
- the Neon `production`, `preview-base`, pre-cutover checkpoint, and two no-TTL production
  recovery branches remain ready;
- Heroku pipeline `inkcre-core` contains exactly the native core and PostgREST production
  apps, both container-based, addon-free, Eco, and up;
- live core readiness reports contract `peer-database-runtime-v1`, environment `production`,
  migration current/expected `d9f4e2a1b7c3`, and healthy roles, privileges, and catalogs;
  unauthenticated PostgREST returns HTTP 401.

Cloudflare Pages activation is not a retirement gate. The static deployment controllers are
checked in and green when the optional provider is unconfigured; account verification and
project creation remain an explicit human follow-up.
