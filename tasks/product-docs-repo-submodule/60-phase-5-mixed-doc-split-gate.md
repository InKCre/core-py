# Phase 5: Mixed Doc Split Gate

## Goal

Split the remaining mixed docs without centralizing `core-py`-local truth into `InKCre/docs` and without degrading local readability.

## Remaining Mixed Inputs

- `docs/20-product-tdd/info-base-ingestion.md`

## First-Principles Gate

A statement may move into `InKCre/docs` only if all of the following are true:

1. another unit repo or shared product memory actually needs it
2. it can be written without depending on `core-py`-local class names, method names, or table names unless those names are themselves the durable contract
3. the remaining local details still have a readable home after extraction
4. the split reduces ambiguity instead of creating twin docs that say nearly the same thing

If any gate fails, keep the statement local and improve the local container first.

## Current Risk Assessment

### `docs/15-alignment/glossary.md`

- status: completed in Phase 5A
- result: shared terms stayed in `InKCre/docs/15-alignment/product-glossary.md`; implementation terms were redistributed into local guides and the mixed file was removed

### `docs/20-product-tdd/extension-runtime.md`

- status: completed in Phase 5B
- result: shared state semantics moved into `InKCre/docs/20-product-tdd/system-state-and-authority.md` and `InKCre/docs/20-product-tdd/cross-unit-contracts.md`; local runtime mechanics were absorbed into `app/business/extension/AGENTS.md`; the mixed local doc was removed

### `docs/20-product-tdd/info-base-ingestion.md`

- shared admission: partial and not yet fully proven
- reason: some ownership statements may be durable across units, but current file still depends heavily on `core-py` managers and resolver/storage internals
- blocking risk: local target container (`app/business/info_base/AGENTS.md`) is not yet in a strong v9.2 shape

## Required Precondition Before Execution

Normalize local containers before extracting shared truth:

1. keep `app/business/info_base/AGENTS.md` in a v9.2 local-guide shape before extracting more ingestion mechanics
2. keep `app/business/extension/AGENTS.md` as the primary local sink for extension runtime details
3. update inbound links so no root guide points at mixed docs as if they were shared truth

## Preferred Split Principle

- shared repo receives only durable contract slices
- local AGENTS receive runtime hazards, implementation vocabulary, manager-level flow, and code-anchored mechanics
- after links are updated, prefer deleting emptied mixed docs instead of keeping redirect stubs unless a short-lived migration stub is strictly necessary

## Exit Criteria

- every remaining mixed statement has one owner
- no shared doc in `InKCre/docs` depends on `core-py`-only implementation detail
- local readers can still find local hazards without opening the shared repo first
