# Docker

## Artifact Contract

The multi-stage `Dockerfile` builds one provider-neutral OCI source with two final process
targets:

- `web`: defaults to `python scripts/container.py web`
- `release`: can only run `python scripts/container.py migrate`

- Python and PDM versions are pinned by `.python-version` and the Docker build argument
- production dependencies come only from the frozen root `pdm.lock`
- the final image contains core code, shared libraries, checked-in extensions, prompts,
  Alembic configuration, and every migration revision
- extension-local virtual environments and locks are not image inputs
- the final process runs as the non-root `inkcre` user

Both targets share the entry point `python scripts/container.py`. Supported commands are:

- `web`: start Uvicorn on `0.0.0.0:$PORT`
- `migrate`: run `alembic upgrade head`
- `ready`: check database connectivity and exact Alembic head without writing

The artifact never generates migrations or downloads extension code.

## Local Compose

`docker-compose.yml` defines:

- `postgres`: PostgreSQL 17 with pgvector and a health check
- `migrate`: a one-shot instance of the exact application image
- `app`: the same image in `web` mode, started only after migration succeeds

Start the stack:

```bash
docker compose up --build
```

Override local ports with `POSTGRES_PORT` and `APP_PORT`. Compose defaults are development
only; production credentials must come from the deployment platform.

## Health Semantics

- `/livez` is process-only
- `/readyz` requires a migrated database and completed runtime bootstrap
- the Compose health check deliberately uses liveness; routing platforms should use
  readiness before sending traffic

## CI Evidence

The artifact job in `.github/workflows/ci.yml` builds the frozen image, inspects required
paths, migrates a fresh pgvector database, runs `alembic check`, starts the web command on a
dynamic port, and probes both liveness and readiness.

When no local Docker-compatible runtime is installed, this CI job is the authoritative
container execution proof.
