# Task: Product Docs In `.github` With Read-Only Mirrors

## Status

Exploration.

This task stays in `tasks/` because the migration boundary, file classification, and sync contract are still under review.

## Objective

Make `InKCre/.github` the single authoring source for product-scope durable docs, while keeping unit repos locally readable through committed read-only mirrors instead of Git submodules.

## Fixed Constraints

- `InKCre/.github` is the required source repository for product-scope durable docs.
- Git submodules are rejected.
- Unit repos must remain self-contained after a normal clone.
- `core-py` keeps unit-local runtime and implementation memory local.

## Folder Map

- `00-phase-map.md`: execution phases, dependencies, and review gates
- `10-phase-0-classification-gate.md`: file-by-file classification work before any migration
- `20-phase-1-source-namespace.md`: source layout and ownership model inside `.github`
- `30-phase-2-mirror-contract.md`: mirror policy, manifest shape, and stamping rules
- `40-phase-3-sync-automation.md`: sync script, workflow, and PR fan-out plan
- `50-phase-4-core-py-rollout.md`: staged rollout plan for `core-py`
- `60-phase-5-guards-and-ops.md`: CI guards, edit protection, and operating model
- `90-review-checklist.md`: cross-phase questions for human review

## Current Working Position

The direction is:

- centralize product-scope durable docs in `.github`
- do not use submodules
- mirror shared docs into consumer repos as ordinary committed files
- classify current docs file-by-file before moving anything

## Immediate Next Step

Review the phase map and the Phase 0 classification gate first. Migration should not start before Phase 0 is accepted.
