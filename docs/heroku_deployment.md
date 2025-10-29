# Heroku Deployment Guide

This guide explains how to deploy the InKCre Core application to Heroku.

## Prerequisites

- A Heroku account ([sign up here](https://signup.heroku.com/))
- Heroku CLI installed ([installation guide](https://devcenter.heroku.com/articles/heroku-cli))
- Git installed

## Quick Start (One-Click Deploy)

The easiest way to deploy this application is using the Heroku button:

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

This will:
1. Create a new Heroku app
2. Provision a PostgreSQL database
3. Set up the required environment variables
4. Deploy the application

## Manual Deployment

### 1. Create a Heroku App

```bash
heroku create your-app-name
```

### 2. Add PostgreSQL Database

```bash
heroku addons:create heroku-postgresql:essential-0
```

This will automatically set the `DATABASE_URL` environment variable.

### 3. Set Environment Variables

The application requires the `DB_CONN_STRING` environment variable. You can set it to use the Heroku PostgreSQL database:

```bash
# Get the DATABASE_URL
heroku config:get DATABASE_URL

# Set DB_CONN_STRING (you can use the same value as DATABASE_URL)
heroku config:set DB_CONN_STRING=$(heroku config:get DATABASE_URL)
```

If you have other environment variables needed by the application, set them now:

```bash
heroku config:set VARIABLE_NAME=value
```

### 4. Deploy the Application

```bash
git push heroku main
```

Or if you're working on a different branch:

```bash
git push heroku your-branch-name:main
```

### 5. Run Database Migrations

Database migrations are automatically run during the release phase (before the web dyno starts), so you don't need to run them manually. However, if you need to run them manually:

```bash
heroku run alembic upgrade head
```

### 6. Check the Application

Open your application in a browser:

```bash
heroku open
```

Or check the heartbeat endpoint:

```bash
curl https://your-app-name.herokuapp.com/heartbeat
```

## Files Added for Heroku Deployment

### Procfile
Defines how Heroku runs the application:
- `release`: Runs database migrations before deploying
- `web`: Starts the uvicorn server

### runtime.txt
Specifies the Python version (3.12.3)

### requirements.txt
Lists all Python dependencies. Generated from `pyproject.toml`.

### app.json
Configuration for one-click deployment, including:
- Required environment variables
- PostgreSQL addon
- Default dyno formation

## Scaling

To scale your application:

```bash
# Scale web dynos
heroku ps:scale web=2

# Check current dyno status
heroku ps
```

## Viewing Logs

```bash
# View recent logs
heroku logs --tail

# View logs from the release phase
heroku logs --source=release --tail
```

## Troubleshooting

### Database Connection Issues

If you have database connection issues, verify the `DB_CONN_STRING` is set correctly:

```bash
heroku config:get DB_CONN_STRING
```

### Migration Issues

Check the release phase logs:

```bash
heroku logs --source=release
```

### Application Crashes

Check the application logs:

```bash
heroku logs --tail --dyno=web
```

## Environment Variables

The application uses the following environment variables:

- `DB_CONN_STRING` (required): PostgreSQL connection string
- `PORT` (auto-set by Heroku): Port the application listens on

Add any additional environment variables your application needs using:

```bash
heroku config:set VARIABLE_NAME=value
```

## Resources

- [Heroku Python Documentation](https://devcenter.heroku.com/categories/python-support)
- [Heroku PostgreSQL Documentation](https://devcenter.heroku.com/articles/heroku-postgresql)
- [FastAPI Deployment Documentation](https://fastapi.tiangolo.com/deployment/)

## Notes

- The application uses PostgreSQL with pgvector extension. Ensure your Heroku PostgreSQL plan supports extensions.
- The free tier of Heroku PostgreSQL has been discontinued. The minimum plan is `essential-0`.
- Consider using a higher-tier plan for production workloads.
