# Deployment And Runtime Docs

This layer stores operational truth: how the service starts, how environments are configured, and which checked-in files or workflows define deployment behavior.

## Documents

- [development-environment.md](development-environment.md)
- [database-contract.md](database-contract.md)
- [docker.md](docker.md)
- [extension-targets.md](extension-targets.md)
- [heroku.md](heroku.md)
- [neon.md](neon.md)
- [runtime-orchestration.md](runtime-orchestration.md)

## Checked-In Runtime Anchors

- `run.py`
- `.python-version`
- `.env.example`
- `Dockerfile`
- `Dockerfile.postgrest`
- `docker-compose.yml`
- `svc.json`
- `scripts/dev_database.py`
- `scripts/dev_database_provider.py`
- `scripts/remote-compose.sh`
- `.github/workflows/branching-database.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/artifact-publish.yml`
- `extensions/twitter/target-publish.json`
- `scripts/build_extension_target.py`
- `.github/actions/preview-verify/action.yml`
- `.github/actions/preview-delivery/action.yml`
- `.github/workflows/preview-deploy.yml`
- `.github/workflows/production-deploy.yml`
- `scripts/generate-openapi.py`
- `docs/openapi.json`
