# Phase 0 Result: `core-py/docs` Classification (Snapshot: 2026-04-01)

## File-by-File Classification Table

| current path | declared layer | actual scope | owner repo | target location | action | rationale |
| --- | --- | --- | --- | --- | --- | --- |
| `docs/10-prd/core-product.md` | PRD | product | `InKCre/docs` | `InKCre/docs/10-prd/core-product.md` | move (light edit) | Core content is product semantics and invariants; only minor local wording leak exists (`core-py` sentence). |
| `docs/15-alignment/glossary.md` | alignment | mixed | split (`InKCre/docs` + `core-py`) | `InKCre/docs/15-alignment/product-glossary.md` and local AGENTS/alignment notes in `core-py` | split + move | Contains product terms and Python/table/class terms in one file. |
| `docs/20-product-tdd/extension-runtime.md` | product-tdd | mixed | split (`InKCre/docs` + `core-py`) | `InKCre/docs/20-product-tdd/extension-cross-unit-contract.md` and `app/business/extension/AGENTS.md` | split + move | Cross-unit statements are mixed with runtime internals anchored only to `core-py` code paths. |
| `docs/20-product-tdd/info-base-ingestion.md` | product-tdd | mixed | split (`InKCre/docs` + `core-py`) | `InKCre/docs/20-product-tdd/info-base-cross-unit-contract.md` and `app/business/info_base/AGENTS.md` | split + move | Some statements are durable cross-unit semantics, but many are local manager-level implementation constraints. |
| `docs/20-product-tdd/runtime-orchestration.md` | product-tdd | unit-local | `core-py` | `docs/40-deployment/runtime-orchestration.md` (or equivalent local runtime doc) | move (local relayer) | Startup order, scheduler cadence, and OpenAPI generation flow are this service runtime truths. |
| `docs/40-deployment/README.md` | deployment | unit-local | `core-py` | keep current path | keep | Local runtime anchor map for this unit repo. |
| `docs/40-deployment/development-environment.md` | deployment | unit-local | `core-py` | keep current path | keep | Local env, CI DB branch flow, and hosted setup are repo-specific operations. |
| `docs/40-deployment/docker.md` | deployment | unit-local | `core-py` | keep current path | keep | Container build/runtime model is implementation and deployment local to this unit. |
| `docs/40-deployment/heroku.md` | deployment | unit-local | `core-py` | keep current path | keep | Heroku process/addon/release semantics are deployment-local. |
| `docs/40-deployment/neon.md` | deployment | unit-local | `core-py` | keep current path | keep | Neon scale-to-zero behavior and workflow references are local ops truths. |
| `docs/_svc_v9_2.md` | framework reference | cross-unit (meta) | `InKCre/docs` | `InKCre/docs/00-meta/_svc_v9_2.md` | move (meta track) | This is collaboration framework truth, not product PRD/TDD/deployment truth. |
| `docs/openapi.json` | generated artifact | unit-local | `core-py` | keep current path | keep (exclude from shared docs transport) | Generated API schema tied to this service build and CI flow. |

## Mixed File Split Notes

### `docs/15-alignment/glossary.md`

- Move product/domain terms to `InKCre/docs/15-alignment/product-glossary.md`.
- Move Python package, ORM model, and DB table naming notes to local context near code (`app/**/AGENTS.md`), not product alignment.

### `docs/20-product-tdd/extension-runtime.md`

- Keep only cross-unit stable contract points in shared Product TDD (`InKCre/docs/20-product-tdd`).
- Move startup lifecycle details, manager method expectations, and runtime mutation hazards to `app/business/extension/AGENTS.md`.

### `docs/20-product-tdd/info-base-ingestion.md`

- Keep only cross-unit ownership boundaries and durable data authority rules in shared Product TDD (`InKCre/docs/20-product-tdd`).
- Move manager/resolver/storage operational mechanics and local failure hazards to `app/business/info_base/AGENTS.md` (and adjacent local AGENTS where needed).

## Terminology Collision Check

- `info-base` (domain concept) vs `info_base` (Python module path).
- `extension` (product capability) vs `Extension` runtime class + `extensions` table row.
- `source collect job` (domain lifecycle unit) vs `sources_collect_jobs` table record.
- `block content` (stored field) vs `raw content` (storage fetch output) vs `solved content` (resolver interpretation).
- `core product` naming currently blends product-wide semantics with unit identity (`core-py` wording).

## Pilot Batch Candidate (`shared-now` Only)

- `docs/10-prd/core-product.md` after light wording cleanup.

## Out Of Pilot (Need Split First)

- `docs/15-alignment/glossary.md`
- `docs/20-product-tdd/extension-runtime.md`
- `docs/20-product-tdd/info-base-ingestion.md`

## Notes

- This classification is a Phase 0 task artifact only; it does not change durable docs yet.
- If this table is accepted, Phase 1 can define source boundary with this ownership map as input.
