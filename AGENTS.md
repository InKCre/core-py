## Project Overview

This is the Python implementation of InKCre. 
InKCre aims to build an information management application that provides automatic information collection, organization and powerful use of information. 

## Tech Stack

- API Framework: FastAPI
- Background Task: Apscheduler
- Database management: SQLModel as ORM, Alembic as migration tool
- Database: PostgreSQL
- Configuration management: pydantic-settings + env file

## Business Domains

- source: Data collectors, the input of info-base
- info-base
  - block: Content units
  - relation: Links between blocks
  - storage: Store block content somewhere else than database.
  - resolver: resolves block content
- sink: Interface to use information base, the output of info-base
- extension: extends info-base, source and sink abilities

## Project Structure

- `pyproject.toml`
- `requirements.txt`: the prod requirements generated from `pyproject.toml` using PDM.
- `run.py`: include routes and launch the app
- `app/`
  - `business/`: service layer, by domains
  - `schemas/`: tables and data models
  - `routes/`: register/wrap/expose business methods to FastAPI
  - `engine.py`: db session
  - `settings.py`: centeralized application settings based on pydantic-settings
  - `scheduler.py`: apscheduler
- `extensions/`: built-in extensions (also where installed extensions stored)
- `utils/`
- `libs/`
  - `obsrv`: observability
  - `ai`: embedding, LLM completion
- `tests/`: unit tests
- `migrations/`: db migrations
- `scripts/`
- `docs/`

## Development Workflow

- Package management: Use PDM (`pdm run` for scripts/executables)
- Database Migrations: `pdm run alembic-gengrade "message"` (autogenerates + upgrades)
- Run dev server: `uvicorn run:api_app --reload` (sets up extensions, scheduler)

## Coding Guideline

- Do not repeat yourself.
  - If the same code is used at over two places, extract it.

## Deployment

This project supports following deployments:

- Heroku App
- Docker Compose / Docker