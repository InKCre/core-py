# Implementation Audit Scope Boundary

## Purpose

Record the implementation drifts discovered while checking `docs/30-unit-tdd/business-pipeline-and-authority.md` and related local guides against code, without pulling volatile code-fix work back into this SVC v9.3 documentation task.

## Decision

This task remains **docs-only**.

It applies SVC v9.3 layering and routing. It does **not** modify production code in `app/business/**`.

## Why

The drifts found during implementation review are real, but they are code-maintenance work, not durable-doc placement work.

Under SVC v9.3, code bugs and legacy implementation seams should not be "fixed" by rewriting durable docs to mirror the bug. They should either:

- be corrected in code and tests in a separate execution task, or
- remain recorded here in `tasks/` as volatile follow-up memory

## Drifts Found

### 1. Embedding upsert call shape

- `app/business/info_base/block.py` currently calls `EmbeddingManager.upsert_block_embedding(...)` with positional arguments that do not match the current signature in `app/business/sink/embedding.py`.
- This is an implementation drift against the documented authority that info-base may trigger sink-owned embedding upsert during block persistence.

### 2. Extension running-state checks

- `app/business/extension/main.py` checks `RUNNING_EXTENSIONS` using the extension class object, while the registry is keyed by extension ID.
- This is an implementation bug in runtime lifecycle bookkeeping, not a reason to weaken the unit-level architecture doc.

### 3. Legacy resolver/storage API remnants

- several built-in resolvers still look shaped for older storage APIs or incomplete resolver contracts
- this includes missing/legacy methods in built-in resolver files and stale references to storage helpers that no longer match the current storage manager shape

### 4. Source scheduling remains undecided

- the current dual-path source scheduling situation was reconfirmed
- but the scheduling cleanup decision remains outside this task

## Explicit Non-Actions

- do not change `docs/30-unit-tdd/` to normalize these bugs into durable architecture
- do not rewrite local `AGENTS.md` to preserve temporary broken behavior as if it were stable truth
- do not change production code here

## Follow-Up Shape

If this work is reopened later, split it into separate tasks:

1. code/task for embedding and extension lifecycle correctness
2. code/task for resolver/storage legacy cleanup
3. separate decision task for source scheduling convergence
