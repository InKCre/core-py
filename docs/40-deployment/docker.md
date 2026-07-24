# Docker

## Artifact Contract

The multi-stage `Dockerfile` builds one provider-neutral OCI source with three delivery
targets:

- `artifact`: the default provider-neutral image with the strict container entry point
- `heroku-web`: a Heroku-adapted image whose full command starts the web process
- `heroku-release`: a Heroku-adapted no-op release guard; the protected delivery job runs
  database lifecycle commands without placing owner credentials in Heroku config

- Python and PDM versions are pinned by `.python-version` and the Docker build argument
- production dependencies come only from the frozen root `pdm.lock`
- the final image contains core code, shared libraries, checked-in extensions, prompts,
  Alembic configuration, and every migration revision
- extension-local virtual environments and locks are not image inputs
- the final process runs as the non-root `inkcre` user

The default artifact entry point is `python scripts/container.py`. Supported commands are:

- `web`: start Uvicorn on `0.0.0.0:$PORT`
- `db <command>`: run the explicit lifecycle surface documented in
  [database-contract.md](database-contract.md)
- `ready`: compatibility entry point for runtime-profile database readiness

The artifact never generates migrations or downloads extension code.

The two Heroku targets contain identical application files and dependencies, plus `curl`.
They clear the inherited entry point because Heroku executes container commands through its
runtime wrapper. The release target is deliberately harmless: Heroku config vars are shared
by every dyno in an app, so putting a migration owner URL there would also expose it to the
web process.

`Dockerfile.postgrest` wraps the digest-pinned upstream PostgREST image only to bind its
server port to Heroku's runtime `$PORT`. JWT and database configuration remain runtime
inputs.

## Local Compose

`docker-compose.yml` defines:

- `postgres`: digest-pinned PostgreSQL 17 with pgvector and a health check
- `init`: a one-shot development-profile lifecycle initializer
- `app`: the same image using the unprivileged `inkcre_core` login
- `postgrest`: digest-pinned PostgREST using the unprivileged `authenticator` login

Start the stack:

```bash
docker compose up --build
```

Override local ports with `POSTGRES_PORT`, `APP_PORT`, and `POSTGREST_PORT`. Set
`INKCRE_COMPOSE_PROJECT_NAME` to give each worktree or agent a separate network and volume:

```bash
INKCRE_COMPOSE_PROJECT_NAME=inkcre-agent-a \
POSTGRES_PORT=55432 APP_PORT=58000 POSTGREST_PORT=53000 \
docker compose up --build
```

Cleanup is bounded by the same project identity:

```bash
docker compose -p inkcre-agent-a down --volumes
```

Compose defaults are development-only; production credentials come from protected runtime
secrets.

## Health Semantics

- `/livez` is process-only
- `/readyz` requires a migrated database and completed runtime bootstrap
- the Compose health check deliberately uses liveness; routing platforms should use
  readiness before sending traffic

## CI Evidence

The artifact job in `.github/workflows/ci.yml` builds the frozen image and proves the full
fresh-database chain: duplicate init, JSON readiness, negative drift cases, PostgREST JWT
read/write and denial behavior, duplicate deterministic reset, Alembic metadata, and web
liveness/readiness. It uses no Neon or Heroku state.

After that workflow passes on the exact current `main`, `artifact-publish.yml` publishes the
runtime to GHCR by commit and reports the immutable digest.

When no local Docker-compatible runtime is installed, this CI job is the authoritative
container execution proof.
