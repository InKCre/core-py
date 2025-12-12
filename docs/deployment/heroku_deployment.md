# Heroku Deployment Guide

This guide explains how to deploy the InKCre Core to Heroku.

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

You can create a new Heroku PostgreSQL add-on attached to the app by:
```bash
heroku addons:create heroku-postgresql:standard-0 -a ${YOUR_APP_NAME}
```

> It's recommended to use `standard-x` plan but not `essential-x` plan since `esstential` level does not support multiple credentials which make PostgREST not possible. 

### 3. Set Environment Variables

The application uses the `DATABASE_URL` environment variable to connect to the database. 

If you are using Heroku PostgreSQL add-on, `DATABASE_URL` will be automatically configured.

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

## Additional Features

### Logtail (Better Stack)

### PostgREST

> Read [Deploy PostgREST on Heroku](https://docs.postgrest.org/en/v11/integrations/heroku.html) for more.

1. Create a new Heroku App
```bash
heroku apps:create ${YOUR_APP_NAME} --buildpack https://github.com/PostgREST/postgrest-heroku.git`
git init
heroku git:remote -a ${YOUR_APP_NAME}
```
2. `vi Procfile`, write

```
web: PGRST_SERVER_HOST=0.0.0.0 PGRST_SERVER_PORT=${PORT} PGRST_DB_URI=${PGRST_DB_URI:-${DATABASE_URL}} ./postgrest-${POSTGREST_VER}
```

3. Set following env var

```bash
heroku config:set POSTGREST_VER=11.2.1
heroku config:set PGRST_DB_SCHEMA=public
heroku config:set PGRST_DB_ANON_ROLE=anonymous
heroku config:set PGRST_JWT_SECRET=   # keep the same as .env
heroku config:set PGRST_DB_URI=postgresql://  # set this if you are using PostgreSQL deployed elsewhere
```

4. Build and deploy

```bash
git add Procfile
git commit -m "init"
git push heroku master
```


If you are using Heroku PostgreSQL:
1. `heroku pg:credentials:create --name anonymous -a ${YOUR_APP_NAME}`
2. `heroku pg:credentials:create --name authenticated -a ${YOUR_APP_NAME}`
3. `heroku addons:attach ${HEROKU_PG_DB_NAME} --credential anonymous -a ${YOUR_APP_NAME}`
4. `heroku addons:attach ${HEROKU_PG_DB_NAME} --credential authenticated -a ${YOUR_APP_NAME}`

Run following SQL commands using default credential:

```sql
GRANT usage on schema public to authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;

-- For future tables in schema public
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;
```

## Files Added for Heroku Deployment

### Procfile
Defines how Heroku runs the application:
- `release`: Runs database migrations before deploying
- `web`: Starts the uvicorn server

### .python-version
Specifies the Python version.

### requirements.txt
Lists all Python dependencies. Generated from `pyproject.toml` using `pdm export -o requirements.txt --prod`.

Normally, git hooks will export the requirements.txt file.

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

## References

- [Heroku Python Documentation](https://devcenter.heroku.com/categories/python-support)
- [Heroku PostgreSQL Documentation](https://devcenter.heroku.com/articles/heroku-postgresql)
- [FastAPI Deployment Documentation](https://fastapi.tiangolo.com/deployment/)

## Notes

- The application uses PostgreSQL with pgvector extension. Ensure your Heroku PostgreSQL plan supports extensions.
