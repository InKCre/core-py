# Phase Map

## Purpose

This file is the execution index for the task. It shows phase order, hard dependencies, expected outputs, and review gates.

## Phase Sequence

### Phase 0: Classification Gate

Goal:

- decide what is product-shared, unit-local, or split-required

Required output:

- a file-by-file classification table for current `core-py/docs`

Review gate:

- no migration work starts before this table is accepted

### Phase 1: Source Namespace In `.github`

Goal:

- define where product durable docs live inside `.github`

Required output:

- one source subtree layout
- one ownership README for that subtree

Dependency:

- depends on Phase 0

### Phase 2: Mirror Contract

Goal:

- define what gets mirrored, how it is stamped, and where it lands in consumer repos

Required output:

- mirror manifest schema
- mirror file stamp format
- local-vs-mirrored directory policy

Dependency:

- depends on Phase 1

### Phase 3: Sync Automation

Goal:

- define how source changes become consumer-repo PRs

Required output:

- sync script design
- workflow design
- auth and PR strategy

Dependency:

- depends on Phase 2

### Phase 4: `core-py` Rollout

Goal:

- onboard the first consumer repo safely

Required output:

- migration sequence for `core-py`
- rollback path
- post-rollout verification list

Dependency:

- depends on Phase 3

### Phase 5: Guards And Operations

Goal:

- prevent drift after rollout

Required output:

- CI guard policy
- local edit policy
- operating instructions for maintainers

Dependency:

- depends on Phase 4

## Cross-Phase Rules

- do not migrate by directory name alone
- do not centralize unit-local docs accidentally
- keep `core-py` readable without extra clone flags
- prefer one stable automation path over many ad hoc sync mechanisms

## Suggested Review Order

1. `10-phase-0-classification-gate.md`
2. `20-phase-1-source-namespace.md`
3. `30-phase-2-mirror-contract.md`
4. `40-phase-3-sync-automation.md`
5. `50-phase-4-core-py-rollout.md`
6. `60-phase-5-guards-and-ops.md`
7. `90-review-checklist.md`
