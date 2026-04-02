# Phase Map

## Objective

Reach an accepted distribution architecture for product docs authored in `InKCre/docs` and consumed by `core-py`, with reliability constraints explicit and testable.

## Phase Sequence

### Phase 0: Classification Gate

Output:

- per-file ownership table for current `core-py/docs`

Gate:

- no transport mechanism decision is finalized before ownership is classified

### Phase 1: Source Boundary In `InKCre/docs`

Output:

- source subtree shape for exportable product docs
- explicit in-scope vs out-of-scope content boundary

Dependency:

- Phase 0

### Phase 2: Strategy Decision

Output:

- lock `git submodule` as the single transport strategy
- explicit non-goals to prevent implicit subtree adoption

Dependency:

- Phase 1

### Phase 3: Submodule Reliability Pack

Output:

- SOP for updates and rollbacks
- Agent Skill spec to reduce operator mistakes
- CI guard spec for pointer integrity

Dependency:

- Phase 2

### Phase 4: `core-py` Pilot Rollout

Output:

- first rollout sequence, verification checklist, rollback path

Dependency:

- Phase 3 complete

### Phase 5: Split Remaining Mixed Docs

Output:

- explicit shared-admission gate for mixed docs
- per-section split matrix for remaining mixed files
- execution order that upgrades local containers before shared extraction

Dependency:

- Phase 4 complete

## Cross-Phase Invariants

- do not move docs by folder name alone
- keep local runtime/deployment docs local
- avoid document sprawl in task artifacts
- every automation rule must have a concrete failure mode and recovery step

## Current Progress

- Phase 0 completed.
- Phase 1~3 local artifacts recorded in `31-phase-1-3-execution-output.md`.
- Phase 4 rollout recorded in `51-phase-4-execution-output.md` and already pushed to `develop`.
- Phase 5 planning recorded in `60-phase-5-mixed-doc-split-gate.md` and `61-phase-5-split-matrix.md`.
- Phase 5A execution recorded in `62-phase-5a-execution-output.md`.
- Phase 5B execution recorded in `63-phase-5b-execution-output.md`.
