# InKCre Core

Python backend implementation of InKCre, built with FastAPI, SQLModel, APScheduler, and PostgreSQL.

## Local Start

```bash
cp .env.example .env
pdm install -G dev
pdm run uvicorn run:api_app --reload
```

Developer setup and shared-skill notes: [CONTRIBUTING.md](CONTRIBUTING.md)

## Documentation Map

If `docs/_shared/` is missing, run `git submodule update --init --recursive` before following shared-doc links.

- Agent operating guide: [AGENTS.md](AGENTS.md)
- Shared framework baseline: [docs/_shared/00-meta/_svc_v9_2.md](docs/_shared/00-meta/_svc_v9_2.md)
- Shared product truth: [docs/_shared/10-prd/core-product.md](docs/_shared/10-prd/core-product.md)
- Shared product glossary: [docs/_shared/15-alignment/product-glossary.md](docs/_shared/15-alignment/product-glossary.md)
- Shared cross-unit technical truth: [docs/_shared/20-product-tdd/](docs/_shared/20-product-tdd/)
- Deployment and runtime truth: [docs/40-deployment/README.md](docs/40-deployment/README.md)
- Volatile plans and backlog: [tasks/](tasks/)

## Generated Artifacts

- OpenAPI schema: `docs/openapi.json`
