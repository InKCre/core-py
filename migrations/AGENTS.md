# Database Migrations

> Applies to `migrations/` and its revision integrity baseline.

- Generate candidates only after model metadata changes with `pdm run db:generate`; generation never upgrades a database.
- Published revisions are append-only. Never edit, delete, rename, reorder, or regenerate one already admitted by the integrity baseline.
- Review generated DDL, locks, data repair, downgrade behavior, and provider assumptions; then append its digest with `pdm run db:record`.
- Migrations must not create cluster-global roles, embed secrets, or depend on application startup, LLM, logging, or client configuration.
- Only explicit lifecycle/release commands apply checked-in revisions. `Procfile` and deployment must never autogenerate.
- Preview-base sanitization is restricted to its exact named, guarded baseline and is forbidden for production, ordinary preview, and release databases.
- Required check: `pdm run check:migrations`; validate consequential revisions on a disposable PostgreSQL/Neon-compatible database.
