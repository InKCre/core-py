# Phase 5B Execution Output

## Scope

This file records the `extension-runtime` split of Phase 5:

- move shared extension state semantics into `InKCre/docs`
- absorb local runtime mechanics into `app/business/extension/AGENTS.md`
- remove the mixed local Product TDD file

## Shared Contract Output

- updated `InKCre/docs/20-product-tdd/system-state-and-authority.md`
  - extension installation authority is deployment-level and distinct from permission/runtime state
- updated `InKCre/docs/20-product-tdd/cross-unit-contracts.md`
  - `installed` / `enabled` / `running` are explicitly distinct
  - enablement is client-scoped
  - runtime start/stop has capability and API side effects

## Local Output

- updated `app/business/extension/AGENTS.md`
  - local runtime mechanics are now the primary local source
  - method-level state transition behavior stays local
- removed local mixed file:
  - `docs/20-product-tdd/extension-runtime.md`

## Remaining Phase 5 Scope

- `docs/20-product-tdd/info-base-ingestion.md`

This remains gated until its shared slice can be written without `core-py`-only manager and resolver/storage leakage.
