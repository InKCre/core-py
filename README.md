# InKCre Core

Python backend implementation of InKCre, built with FastAPI, SQLModel, APScheduler, and PostgreSQL.

## Local Start

```bash
pdm install -G dev --frozen-lockfile
svc dev ensure database --repo . --json
```

This starts the complete peer runtime: pgvector, deterministic database initialization,
core-py, and PostgREST. Committed configuration uses local Docker; ignored
`svc.local.json` may select a validated SSH Docker provider. For Python-only iteration,
run `pdm run check`, then `pdm run dev` against an initialized database.

`pdm run check` is the hermetic repository contract used by CI: frozen dependency
checks, migration containment, formatting, lint, and the complete unit-test suite.

Developer setup and shared-skill notes: [CONTRIBUTING.md](CONTRIBUTING.md)

## Browser-Only Self-Hosting

A repository owner can deploy their own InKCre instance to Neon and two Render Docker
services without cloning this repository. Forking is the onboarding mechanism; the deployed
instance is independent from InKCre's canonical production environment. Configure the six
documented GitHub Secrets/Variables, then run the checked-in `Deploy self-hosted InKCre`
workflow. The JWT signing secret remains private and grants full Peer authority.

Exact onboarding steps, runtime limits, and cleanup:
[Self-Hosting On Render And Neon](docs/40-deployment/render-neon-self-host.md).

## Security

Report vulnerabilities privately through [SECURITY.md](SECURITY.md). Security-sensitive
design and triage should use the repository's [Core Security
Model](docs/30-unit-tdd/security-model.md) rather than treating hardening practices as
context-free requirements.

## Documentation Map

If `docs/_shared/` is missing, run `git submodule update --init --recursive` before following shared-doc links.

- Agent operating guide: [AGENTS.md](AGENTS.md)
- Working protocol: run `svc status . --json`, then read `index.md` with
  `svc lookup --path`; the adopted SVC corpus is 14.0.0. Load
  `sub-agents/index.md`, `verification/index.md`, or
  `task-packet/index.md` only when their stated pressure exists.
- Shared Hub/Spoke operations: [docs/_shared/00-meta/](docs/_shared/00-meta/)
- Shared product truth: [docs/_shared/10-prd/index.md](docs/_shared/10-prd/index.md)
- Shared product glossary: [docs/_shared/10-prd/glossary.md](docs/_shared/10-prd/glossary.md)
- Shared cross-unit technical truth: [docs/_shared/20-product-tdd/](docs/_shared/20-product-tdd/)
- Local unit design and security model: [docs/30-unit-tdd/README.md](docs/30-unit-tdd/README.md)
- Deployment and runtime truth: [docs/40-deployment/README.md](docs/40-deployment/README.md)
- Agent-owned volatile task workspaces: [tasks/](tasks/)

## Generated Artifacts

- OpenAPI schema: `docs/openapi.json`
- Regenerate locally with `pdm run python scripts/generate-openapi.py`.
- The repository does not publish hosted API documentation automatically.
