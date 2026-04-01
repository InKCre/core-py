# Heroku

## Checked-In Files

- `Procfile`
- `app.json`
- `requirements.txt`
- `README.md`

## Runtime Model

`Procfile` currently defines:

- `release`: `alembic revision --autogenerate -m "mig" && alembic upgrade head`
- `web`: `uvicorn run:api_app --host=0.0.0.0 --port=${PORT:-8000}`

That means every Heroku release currently attempts to autogenerate and apply a migration before boot.

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

The current release command is convenient but aggressive because it autogenerates migrations during deploy. Change this only deliberately, because it alters deployment semantics.
