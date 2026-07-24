# Development Environment

## Local Requirements

- Python 3.12
- PDM 2.27.0
- a Docker-compatible runtime for the complete local peer stack, or PostgreSQL/pgvector
  supplied separately
- a populated `.env` file

The checked-in Python selector is `.python-version`. The foundation CI uses the same
Python selector and PDM version.

## Local Startup

The supported complete runtime is:

```bash
cp .env.example .env
docker compose up --build
```

It starts PostgreSQL/pgvector, performs deterministic development initialization, then
starts both core-py and PostgREST. Core is available on port 8000 and PostgREST on port 3000
by default.

For Python-only iteration against an already initialized database:

```bash
cp .env.example .env
pdm install -G dev --frozen-lockfile
pdm run doctor
pdm run check
pdm run dev
```

`doctor` and `check` do not start the application or connect to a database. The full
repository contract checks tool versions, lock/export consistency, migration integrity,
formatting, lint, settings isolation, and the complete unit-test suite.

Use narrower read-only checks while iterating:

```bash
pdm run check:foundation
pdm run format:check
pdm run lint
pdm run test
```

The test harness disables dotenv before application imports. Repository checks do not read a
developer `.env` or use its database and API credentials.

## Required Environment Variables

The checked-in baseline is `.env.example`.

Required for direct Python execution:

- `DATABASE_URL`
- `JWT_SECRET`

Lifecycle execution additionally requires:

- `MIGRATION_DATABASE_URL`
- `CORE_DATABASE_PASSWORD`
- `POSTGREST_DATABASE_PASSWORD`

Commonly needed:

- `CLIENT_ID`
- `CLIENT_NAME`
- `CLIENT_BASE_URL`
- `LLM_SP_AK`
- `LLM_SP_BASE_URL`
- `OBSRV__*`

## Database Branch Workflow In CI

The repository currently uses Neon branch automation for pull requests.

- `branching-database.yml` creates or reuses `preview/core-py/pr-<number>` for trusted PRs
- every preview branch is a seven-day child of the sanitized `preview-base`
- the branch workflow only establishes the exact isolated branch identity
- the exact PR artifact owns initialization and readiness during application delivery
- PR close deletes only the matching deterministic Neon branch

## Migration Commands

- `pdm run db:generate "message"` creates a candidate revision for review.
- `pdm run db:record` appends reviewed new revisions to the integrity manifest.
- `pdm run db:migrate` applies checked-in revisions.
- `pdm run db:init --profile development` creates the complete deterministic baseline.
- `pdm run db:ready --profile development --json` verifies it without mutation.
- `pdm run db:reset-dev --confirm reset-development-data` restores the same guarded
  baseline and refuses every non-development database.
- `pdm run check:migrations` checks the local graph, metadata registration, and release
  contract without connecting to a database.
- CI validates `migrations/revision-integrity.json` on pull requests and managed-branch
  pushes. A base branch without the manifest is a one-time hard-cut bootstrap; after that,
  protected entries and revision contents may not be modified, deleted, or renamed.

Generation and application are deliberately separate operations.
