# Development Environment

## Local Requirements

- Python 3.12
- PDM 2.27.0
- PostgreSQL
- a populated `.env` file

The checked-in Python selector is `.python-version`. The foundation CI uses the same
Python selector and PDM version.

## Local Startup

```bash
cp .env.example .env
pdm install -G dev --frozen-lockfile
pdm run doctor
pdm run check:foundation
pdm run dev
```

`doctor` and `check:foundation` do not start the application or connect to a database.
The foundation gate checks tool versions, lock/export consistency, and the migration
contract.

Full diagnostics are intentionally separate:

```bash
pdm run lint
pdm run test
```

They currently expose known legacy lint and extension-test debt and are not part of the
foundation gate. Full test collection can also read `.env`, attempt database access, and
render validation inputs in tracebacks. Until that suite is isolated, do not run it with a
credential-bearing `.env` in shared CI or agent logs.

## Required Environment Variables

The checked-in baseline is `.env.example`.

Required in practice:

- `DATABASE_URL`
- `JWT_SECRET`

Commonly needed:

- `CLIENT_ID`
- `CLIENT_NAME`
- `CLIENT_BASE_URL`
- `LLM_SP_AK`
- `LLM_SP_BASE_URL`
- `OBSRV__*`

## Database Branch Workflow In CI

The repository currently uses Neon branch automation for pull requests.

- `branching-database.yml` creates a schema-only Neon branch for PRs
- the parent branch is the PR base branch, with `develop` as fallback
- the workflow posts schema diffs back to the PR
- PR close deletes the Neon branch

## Migration Commands

- `pdm run db:generate "message"` creates a candidate revision for review.
- `pdm run db:record` appends reviewed new revisions to the integrity manifest.
- `pdm run db:migrate` applies checked-in revisions.
- `pdm run check:migrations` checks the local graph, metadata registration, and release
  contract without connecting to a database.
- CI validates `migrations/revision-integrity.json` on pull requests and managed-branch
  pushes. A base branch without the manifest is a one-time hard-cut bootstrap; after that,
  protected entries and revision contents may not be modified, deleted, or renamed.

Generation and application are deliberately separate operations.
