# Heroku

## Checked-In Files

- `Procfile`
- `app.json`
- `requirements.txt`
- `README.md`

## Runtime Model

`Procfile` currently defines:

- `release`: `alembic upgrade head`
- `web`: `uvicorn run:api_app --host=0.0.0.0 --port=${PORT:-8000}`

The release process applies reviewed, checked-in revisions exactly once before boot. It
never creates a revision at deploy time.

The Python runtime is selected by `.python-version`, which is shared by local tooling and
foundation CI.

## One-Click Deploy

`app.json` provides a Heroku deploy button configuration.

Current checked-in behavior:

- Python buildpack
- one `web` dyno
- `heroku-postgresql:essential-0` addon

## Manual Deploy

```bash
heroku create your-app-name
git push heroku main
```

If needed, run migrations manually:

```bash
heroku run alembic upgrade head
```

## Important Constraint

The checked-in one-click config uses `essential-0`, but multi-credential PostgreSQL workflows such as PostgREST-style role separation need a higher plan. Treat that as a deployment trade-off, not as an undocumented assumption.

## Caution

`alembic upgrade head` is a single-writer release operation. A failed migration fails the
release; application rollback does not automatically reverse the database. Revisions must
therefore be reviewed and verified on a disposable database before deployment.

The checked-in Docker image is not yet the Heroku release artifact and remains outside the
foundation-containment contract.
