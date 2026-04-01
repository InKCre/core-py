# InKCre Core

Python backend implementation of InKCre, built with FastAPI, SQLModel, APScheduler, and PostgreSQL.

## Local Start

```bash
cp .env.example .env
pdm install -G dev
pdm run uvicorn run:api_app --reload
```

## Documentation Map

- Agent operating guide: [AGENTS.md](AGENTS.md)
- Product truth: [docs/10-prd/core-product.md](docs/10-prd/core-product.md)
- Alignment glossary: [docs/15-alignment/glossary.md](docs/15-alignment/glossary.md)
- Cross-unit technical truth: [docs/20-product-tdd/](docs/20-product-tdd/)
- Deployment and runtime truth: [docs/40-deployment/README.md](docs/40-deployment/README.md)
- Volatile plans and backlog: [tasks/](tasks/)

## Generated Artifacts

- OpenAPI schema: `docs/openapi.json`
