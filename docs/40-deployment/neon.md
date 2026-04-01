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

The repository currently relies on schema-only Neon branches for PR and hosted-agent workflows.

## Operational Implication

Neon branch lifecycle and scale-to-zero behavior are deployment truths. They should stay documented here rather than mixed into product docs or task notes.
