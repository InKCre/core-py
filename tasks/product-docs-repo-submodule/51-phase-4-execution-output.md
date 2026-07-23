# Phase 4 Execution Output

## Scope

This file records the concrete `core-py` pilot rollout that consumes shared durable docs from `InKCre/docs` via `docs/_shared`.

## Source Commit Consumed

- source repo: `InKCre/docs`
- source branch: `main`
- source commit: `f72e9b6c1d19a15a46554df09451a4a8b17ec91b`

## Consumer Repo Wiring

- submodule mount: `docs/_shared`
- submodule URL: `https://github.com/InKCre/docs.git`
- consumed shared paths:
  - `docs/_shared/00-meta/**`
  - `docs/_shared/10-prd/**`
  - `docs/_shared/15-alignment/**`
  - `docs/_shared/20-product-tdd/**`

## Local Boundary Changes

- removed local shared-source copies:
  - `docs/_svc_v9_2.md`
  - `docs/10-prd/core-product.md`
- moved unit-local runtime truth:
  - `docs/20-product-tdd/runtime-orchestration.md` -> `docs/40-deployment/runtime-orchestration.md`
- updated routing docs:
  - `AGENTS.md`
  - `README.md`
  - `docs/40-deployment/README.md`
  - `app/business/extension/AGENTS.md`

## Validation

- submodule check passed:
  - `check-submodule.sh --mode pre-bump`
  - `check-submodule.sh --mode pre-commit`
- actual mounted commit:
  - `f72e9b6c1d19a15a46554df09451a4a8b17ec91b`

## Deliberate Non-Goals In This Pilot

- no split of mixed local/shared docs yet:
  - `docs/15-alignment/glossary.md`
  - `docs/20-product-tdd/extension-runtime.md`
  - `docs/20-product-tdd/info-base-ingestion.md`
- no repo-local CI workflow added yet; pilot relies on SOP + Agent Skill validation
