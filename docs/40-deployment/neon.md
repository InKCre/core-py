# Neon

## Why This Doc Exists

Neon is part of the repository's operational model, both for runtime compatibility and for branch-based CI workflows.

## Scale-To-Zero Compatibility

If the database can scale to zero when idle, set:

```bash
DATABASE_SCALE_0=true
```

Current checked-in behavior:

- `app/settings.py` exposes `database_scale_0`
- `app/engine.py` enables `pool_pre_ping` when it is true

This exists to reduce stale-connection failures when the database has gone idle.

## Branching Workflow

Neon branch automation is defined in:

- `.github/workflows/branching-database.yml`
- `.github/workflows/copilot-setup-steps.yml`

Trusted pull requests use one data-free branch named `preview/pr-<number>`:

1. create or update the durable `preview-base` from the current runtime branch, then run
   the guarded sanitizer once to remove every allowlisted application row while preserving
   `alembic_version`
2. create or reuse the deterministic branch with a seven-day TTL
3. install the frozen migration runtime and apply `alembic upgrade head`
4. verify that the branch is at the artifact's exact head
5. publish a credential-free schema diff to the GitHub job summary
6. delete the same deterministic branch when the PR closes

The workflow pins Neon CLI 2.36.0. Connection URLs are consumed only through masked action
outputs and are never written to logs or artifacts.

`preview-base` is a normal Neon branch because schema-only branching is incompatible with
the legacy `authenticated` web role on the current runtime branch. Its one-time bootstrap
copies the source branch internally, immediately truncates every known application table,
and verifies the database remains at the repository head.
Production is not mutated, and production rows never enter a PR-owned branch.

The current Neon free-v3 plan has a protected-branch quota of zero, so provider protection
cannot be enabled on `preview-base`. The sanitizer requires the exact branch name, and the
PR cleanup workflow only targets the `preview/pr-<number>` namespace. Upgrade the Neon plan
or revisit branch protection before broadening administrative access.

Application bootstrap may create its required runtime records after preview deployment, but
production data is never treated as seed data. The production cutover packet must establish
which canonical runtime branch refreshes `preview-base` before `main` CD is enabled.

## Operational Implication

Neon branch lifecycle and scale-to-zero behavior are deployment truths. They should stay documented here rather than mixed into product docs or task notes.
