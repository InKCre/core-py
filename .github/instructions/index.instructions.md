---
applyTo: '**'
---

## Project Overview

This is a Python project. Aim to build an information base to collect, organize information automatically and provide a set of powerful ways to search it.

## Tech Stack

- FastAPI for parsing, routing, handling HTTP, Websocket requests.
- SQLModel for defining database tables, data models.
  - Remeber to use PydanticV2 API.
- Alembic for database migration management.
- Pip and `pyproject.toml` for package management.

## File Structure (Only Curcial Parts)

- run.py : include routes and launch app
- app/
  - business/
  - routes/
  - schemas/ : tables and data models
  - libs/
  - utils/
  - engine.py
- extensions/ : installed extensions (built-in maintained here)
- migrations/

