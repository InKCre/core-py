# API Routes

> Applies to `app/routes/`.

- Routes own HTTP parsing, response mapping, and dependency injection only. Business rules and persistence belong to the owning manager.
- Register core routes in `run.py`; extension routes enter only through the extension lifecycle.
- Authentication is enforced by the current middleware/dependency contract. Do not add endpoint-local alternatives that bypass its peer/JWT semantics.
- Keep OpenAPI synchronized with public route/schema changes using `pdm run python scripts/generate-openapi.py`.
- Required check: run affected route tests and verify `docs/openapi.json` has only intended changes.
