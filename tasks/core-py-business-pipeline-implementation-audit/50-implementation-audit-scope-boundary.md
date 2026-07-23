# Implementation Audit Scope Boundary

## Purpose

Record the implementation drifts discovered while checking `docs/30-unit-tdd/business-pipeline-and-authority.md` and related local guides against code, in a task that is explicitly separate from `core-py-post-split-cleanup`.

## Decision

This task is a separate follow-up.

`core-py-post-split-cleanup` remains a SVC v9.3 adoption task about shared baseline consumption, Unit TDD admission, and local `AGENTS.md` strengthening.

Any code changes or implementation verification work should happen here instead of being folded back into that post-split cleanup task.

## Important Caution

Not every issue found during the audit should be assumed to be a code bug. Some apparent mismatches may come from outdated docs, stale local guides, or legacy notes that no longer describe the current implementation correctly.

So every follow-up item below must be re-verified before code changes are made. The decision shape should be:

- code is wrong and should change, or
- docs / local guides are outdated and should change, or
- both drifted and need to be realigned together

## Why

The drifts found during implementation review are real signals, but they are not automatically durable-doc placement work.

Under SVC v9.3, code bugs and legacy implementation seams should not be "fixed" by rewriting durable docs to mirror the bug. They should either:

- be corrected in code and tests in a separate execution task, or
- be reclassified as documentation drift if the code is actually the more current source of truth

## Audit Leads

### 1. Embedding upsert call shape

- `app/business/info_base/block.py` currently calls `EmbeddingManager.upsert_block_embedding(...)` with positional arguments that appear not to match the current signature in `app/business/sink/embedding.py`.
- This may be a real implementation bug, or a sign that the documented/assumed call contract needs re-verification.

### 2. Extension running-state checks

- `app/business/extension/main.py` checks `RUNNING_EXTENSIONS` using the extension class object, while the registry is keyed by extension ID.
- This looks like a runtime lifecycle bug, but should still be re-verified against the intended registry contract before changing code.

### 3. Legacy resolver/storage API remnants

- several built-in resolvers still look shaped for older storage APIs or incomplete resolver contracts
- this includes missing/legacy methods in built-in resolver files and stale references to storage helpers that no longer match the current storage manager shape
- part of this may be code drift, part of it may be local guide / note drift

### 4. Source scheduling remains undecided

- the current dual-path source scheduling situation was reconfirmed
- but the scheduling cleanup decision remains a separate design/execution question and should not be silently collapsed into this audit

## Explicit Non-Actions

- do not change `docs/30-unit-tdd/` to normalize temporary broken behavior into durable architecture
- do not rewrite local `AGENTS.md` to preserve a bug as if it were stable truth
- do not assume every mismatch is a code bug before re-checking whether the docs are outdated

## Follow-Up Shape

If this work proceeds later, split it into separate execution slices such as:

1. code/task for embedding and extension lifecycle correctness
2. code/task for resolver/storage legacy cleanup
3. separate decision task for source scheduling convergence
