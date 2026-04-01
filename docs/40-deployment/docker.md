# Docker

## Checked-In Files

- `Dockerfile`
- `docker-compose.yml`
- `.env.example`

## Current Container Model

The repository ships a multi-stage Dockerfile:

- builder stage installs core and extension dependencies with PDM
- final stage copies the virtualenv and application code

The final image copies core code, migrations, and shared utilities. It does not bake the `extensions/` directory into the final image.

## Docker Compose Model

`docker-compose.yml` currently defines:

- `postgres`: PostgreSQL 17 with health checks
- `app`: the backend service built from the local Dockerfile

Notable runtime behavior:

- `.env` is loaded for both services
- `DATABASE_URL` is overridden inside the app container to point at the compose `postgres` service
- local `./extensions` is mounted into `/app/extensions`

## Migrations

Docker Compose does not run Alembic automatically.

Run migrations explicitly:

```bash
docker-compose exec app alembic upgrade head
```

## Operational Notes

- If extension dependencies change, rebuild the image
- If ports conflict, adjust `docker-compose.yml`
- If extensions fail to load, check that the mounted `extensions/` directory is valid
