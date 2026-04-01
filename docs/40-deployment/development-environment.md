# Development Environment

## Local Requirements

- Python 3.12
- PDM
- PostgreSQL
- a populated `.env` file

## Local Startup

```bash
cp .env.example .env
pdm install -G dev
pdm run uvicorn run:api_app --reload
```

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

## Agent / Hosted Setup

`copilot-setup-steps.yml` currently:

- checks out the repo
- creates a schema-only Neon branch for the current branch
- writes the resulting `DATABASE_URL` to `.env`
- installs project dependencies with PDM

This file is the checked-in truth behind the old "development requires a prepared database branch" note.
