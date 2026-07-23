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

Trusted pull requests use one schema-only branch named `preview/pr-<number>`:

1. map Git base `main` to the current Neon `master` branch; map other base names directly
2. create or reuse the deterministic branch with a seven-day TTL
3. install the frozen migration runtime and apply `alembic upgrade head`
4. verify that the branch is at the artifact's exact head
5. publish a credential-free schema diff to the GitHub job summary
6. delete the same deterministic branch when the PR closes

The workflow pins Neon CLI 2.36.0. Connection URLs are consumed only through masked action
outputs and are never written to logs or artifacts.

Schema-only preview branches do not contain production records. Application bootstrap may
create its own required runtime records after deployment, but production data is neither
copied nor treated as seed data.

The `main` → `master` mapping is transitional. The production cutover packet must establish
and document the canonical production Neon branch before `main` CD is enabled.

## Operational Implication

Neon branch lifecycle and scale-to-zero behavior are deployment truths. They should stay documented here rather than mixed into product docs or task notes.
