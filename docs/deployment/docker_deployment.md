# Docker Deployment Guide for InKCre Core-Py

This guide explains how to deploy the InKCre Core-Py application using Docker, including a PostgreSQL database service.

## Prerequisites

- Docker and Docker Compose installed on your system.
- Git repository cloned locally.

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/InKCre/core-py.git
   cd core-py
   ```

2. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

3. Run database migrations:
   ```bash
   docker-compose exec app alembic upgrade head
   ```

4. The application will be available at `http://localhost:8000`.

4. Access the database at `localhost:5432` with user `inkcre_user`, password `inkcre_password`, database `inkcre`.

## Configuration

### Environment Variables

The following environment variables are set in `docker-compose.yml`:

- `DATABASE_URL`: Connection string for PostgreSQL.

You can override these by creating a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Then edit `.env` with your values. Docker Compose will automatically load variables from `.env`.

### Extensions

Extensions are not included in the Docker image. Instead, they are mounted as a volume from `./extensions` to `/app/extensions` in the container. This allows you to:

- Modify extensions without rebuilding the image.
- Persist extension data.

To add or update extensions:

1. Place extension folders in the `./extensions` directory.
2. Rebuild the image if dependencies change: `docker-compose up --build`.

Note: Extension dependencies are installed during the build process using PDM.

## Build Details

The Dockerfile uses a multi-stage build:

1. **Builder Stage**: Installs core dependencies and extension dependencies using PDM.
2. **Final Stage**: Copies the virtual environment and application code (excluding extensions).

## Database Migrations

Migrations are not automatically run in the container. To run them:

```bash
docker-compose exec app alembic upgrade head
```

Or add a custom entrypoint script if needed.

## Troubleshooting

- **Extensions not loading**: Ensure the `./extensions` folder exists and contains valid extensions. Check container logs: `docker-compose logs app`.
- **Database connection issues**: Verify PostgreSQL is healthy: `docker-compose ps`. Check logs: `docker-compose logs postgres`.
- **Port conflicts**: Change ports in `docker-compose.yml` if 8000 or 5432 are in use.

## Production Considerations

- Use environment-specific `.env` files for secrets.
- Configure proper CORS origins in `run.py`.
- Add health checks and monitoring.
- Use Docker secrets for sensitive data in production.