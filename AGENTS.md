## Project Overview

This is the Python backend of InKCre. InKCre aims to build an information management app-
lication provides powerful and automatical collect, organize and use of information. 

## Tech Stack

- API over HTTP: FastAPI
- ORM and Data models: SQLModel
- database migration: Alembic
- Database: PostgreSQL
- Package management and venv: PDM

## Business Domains

- extension
- info-base
  - block
  - relation
  - storage
  - resolver
  - source
- sink: wrapping the info-base to provide use of information features like querying, insights and more.

## Project Structure

- `pyproject.toml`
- `requirements.txt`: the prod requirements generated from `pyproject.toml` using pdm.
  - Required by Heroku python build pack.
- `run.py`: include routes and launch the app
- `app/`
  - `business/`
  - `schemas/`: tables and data models
  - `routes/`: register/wrap/expose business methods to FastAPI
  - `libs/`
  - `engine.py`: db session
  - `settings.py`: centeralized application settings based on pydantic-settings
  - `scheduler.py`: apscheduler
- `utils/`: utils both app and extensions can use
- `extensions/`: installed extensions (build-in extensions also maintained here)
- `migrations/`: db migrations
