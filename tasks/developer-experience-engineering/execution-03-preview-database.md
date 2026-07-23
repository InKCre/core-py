# Execution 03 — Deterministic Preview Database

## MVT Core

- Objective & Hypothesis: establish one durable, data-free `preview-base`, then give every
  trusted pull request one deterministic disposable branch from that baseline, apply only
  checked-in migrations, publish a reviewable schema diff, and delete the exact same branch
  on close. The hypothesis is that a PR-number identity plus an empty lineage-bearing base
  removes branch-name drift and production-data exposure.
- Guardrails Touched: preview databases contain schema but no production data; the Neon API
  key and connection URL stay masked; migration generation remains forbidden; branch
  cleanup is exact and has TTL fallback; provider CLI versions are pinned.
- Verification: exercise the workflow on PR 17, observe deterministic branch creation or
  reuse, run `alembic upgrade head`, verify exact head, compare schemas, and confirm that
  neither `master` nor `staging` is mutated.

## Classification And Mode

- Reality: the previous workflow created `codex/dx-migration-containment` but failed in the
  schema-diff action; its delete path targeted a different `pr/...` name and would leak the
  created branch.
- Constraint: Neon schema-only branching rejects the legacy `authenticated` role on the
  current `staging` runtime branch. A normal branch must be sanitized once before it can
  become the preview baseline.
- Artifact: deterministic preview-database lifecycle workflow and operational evidence.
- Active modes: Diagnose for the failed workflow, then Execute.

## Impact Handshake

- Target: `.github/workflows/branching-database.yml`, preview-only Neon branches, and local
  deployment documentation.
- Current state: the old PR branch was deleted after its failed migration fully rolled back.
  There is no live PR-owned branch. The workflow uses a stale output name, comments through
  a brittle schema-diff action, and deletes a different branch name.
- Requested operation:
  - use `preview/pr-<number>` for create, reuse, diff, and delete;
  - create `preview-base` from `staging`, sanitize all allowlisted business
    tables while preserving the verified Alembic head, then branch PRs from it;
  - run frozen PDM migration tooling against the action's pooled connection string;
  - write the schema diff to the job summary with pinned Neon CLI 2.36.0;
  - restrict secret-bearing preview creation to branches in this repository;
  - clean the leaked PR-17 branch and let the corrected workflow recreate it.
- Explicit exclusions:
  - no Heroku review app or config mutation in this slice;
  - no production/staging schema or data mutation;
  - no production dump, restore, reset, or cutover;
  - no use of production data as preview seed.
- Invariants:
  - production data remains in the current staging-backed database;
  - migrations are `upgrade head` only;
  - URLs and API keys are never printed or persisted as artifacts;
  - close cleanup and TTL both target the same deterministic branch;
  - `portless.json` remains user-owned and untouched.
- Likely files: `.github/workflows/branching-database.yml`,
  `docs/40-deployment/neon.md`, and this packet.

## Acceptance Criteria

1. PR 17 owns exactly one Neon branch named `preview/pr-17`.
2. `preview-base` is at repository head and every application table has zero rows.
3. The PR branch has a seven-day TTL and is derived from `preview-base`.
4. The action reuses an existing branch on synchronize rather than failing.
5. Frozen repository migration tooling upgrades the preview branch to the repository head.
6. A sanitized schema diff is visible in the GitHub job summary.
7. Closing the PR targets `preview/pr-17`, the same identity used at creation.
8. No production or staging schema or rows are changed by verification.

## Follow-Up Boundary

After this database lifecycle is green, a separate preview-app slice can consume the masked
pooled URL in the same workflow to configure a Heroku review app. Production backup/restore
and `main` cutover remain separate because they have a different recovery and approval
surface.

## Execution Evidence

- Official create-branch action v6 is idempotent by branch name and exposes the pooled URL as
  `db_url_pooled`; the previous workflow used the obsolete `db_url_with_pooler` name.
- Neon CLI 2.36.0 successfully compared `develop` with the first schema-only PR branch,
  proving the provider schema-diff API itself is available.
- The incorrectly named `codex/dx-migration-containment` branch
  (`br-falling-moon-a1lombim`) reported zero written bytes and was deleted. Provider state
  entered `storage_deleted`; it cannot affect `master`, `staging`, or `develop`.
- Free-v3 rejects per-endpoint suspend overrides with `modifying the suspend interval is not
  permitted on this account`; the workflow therefore inherits the project endpoint default
  and relies on exact close cleanup plus the seven-day branch TTL.
- Neon `develop` has an empty `alembic_version` table and is not a valid lineage anchor.
  Read-only readiness verifies `staging` at repository head `a1b2c3d4e5f6`.
- A schema-only branch copies tables but omits the `alembic_version` row, causing
  `upgrade head` to replay the initial revision and fail on existing tables. Direct
  schema-only creation from `staging` is also rejected because of the legacy
  `authenticated` role. The selected hard cut is a sanitized normal branch;
  there is no runtime stamp path.
- Neon free-v3 has a protected-branch quota of zero. `preview-base`
  (`br-misty-base-a1bgexrg`) was therefore created unprotected, sanitized successfully at
  `a1b2c3d4e5f6`, and verified schema-identical to `staging`. The sanitizer's exact-name
  guard and the cleanup workflow's `preview/pr-*` namespace are the current safety boundary.
- `pdm run check` and workflow YAML parsing are green locally. PR synchronization must now
  prove `preview/pr-17` creation, migration, readiness, and schema summary.
