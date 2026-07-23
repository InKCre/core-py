- `versions/`: reviewed, checked-in database schema revisions.
- `settings.py`: migration-only `DATABASE_URL` configuration.
- `metadata.py`: explicit application-table registration for Alembic.
- `env.py`: Alembic offline/online execution.
- `script.py.mako`: template for future candidate revisions.

Generate and review a candidate:

```bash
pdm run db:generate "describe the schema change"
pdm run db:record
```

Apply checked-in revisions separately:

```bash
pdm run db:migrate
```

Release processes apply revisions only. They never generate them.
`db:record` appends new revision digests to `revision-integrity.json` but refuses to
re-record a modified or missing protected revision.
