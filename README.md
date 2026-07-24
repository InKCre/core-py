# InKCre Core

Python backend implementation of InKCre, built with FastAPI, SQLModel, APScheduler, and PostgreSQL.

## Local Start

```bash
cp .env.example .env
docker compose up --build
```

This starts the complete peer runtime: pgvector, deterministic database initialization,
core-py, and PostgREST. For Python-only iteration, install with
`pdm install -G dev --frozen-lockfile`, run `pdm run check`, then `pdm run dev` against an
initialized database.

`pdm run check` is the hermetic repository contract used by CI: frozen dependency
checks, migration containment, formatting, lint, and the complete unit-test suite.

Developer setup and shared-skill notes: [CONTRIBUTING.md](CONTRIBUTING.md)

## Documentation Map

If `docs/_shared/` is missing, run `git submodule update --init --recursive` before following shared-doc links.

- Agent operating guide: [AGENTS.md](AGENTS.md)
- Shared framework baseline: [docs/_shared/00-meta/_svc_v9_8.md](docs/_shared/00-meta/_svc_v9_8.md)
- Shared topology extension: [docs/_shared/00-meta/multi-repo.md](docs/_shared/00-meta/multi-repo.md)
- Shared implementation taste: [docs/_shared/00-meta/implementation-taste.md](docs/_shared/00-meta/implementation-taste.md)
- Shared product truth: [docs/_shared/10-prd/index.md](docs/_shared/10-prd/index.md)
- Shared product glossary: [docs/_shared/10-prd/glossary.md](docs/_shared/10-prd/glossary.md)
- Shared cross-unit technical truth: [docs/_shared/20-product-tdd/](docs/_shared/20-product-tdd/)
- Local unit architecture: [docs/30-unit-tdd/business-pipeline-and-authority.md](docs/30-unit-tdd/business-pipeline-and-authority.md)
- Deployment and runtime truth: [docs/40-deployment/README.md](docs/40-deployment/README.md)
- Agent-owned volatile task workspaces: [tasks/](tasks/)

## Generated Artifacts

- OpenAPI schema: `docs/openapi.json`
- Regenerate locally with `pdm run python scripts/generate-openapi.py`.
- The repository does not publish hosted API documentation automatically.
