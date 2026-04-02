# Meta: Product Docs Distribution From `InKCre/docs`

## Status

Execution (Mode C).

Progress checkpoint:

- Phase 0: completed (classification table done)
- Phase 1~3: executed locally with concrete artifacts in `InKCre/docs`
- Remote `InKCre/docs` created and source boundary pushed
- SOP + Skill baseline completed for Phase 3
- Phase 4 pilot implemented in `core-py` and pushed to `develop`
- Phase 5 split gate recorded for remaining mixed docs
- Phase 5A executed: shared skill relocated, local `info_base` guide upgraded, local mixed glossary removed
- Phase 5B executed: `extension-runtime` split into shared state contract plus local runtime guide

## Intent

Define a robust way to let unit repos consume product-scope docs authored in `InKCre/docs`.

## Fixed Constraints

- Source repository stays `InKCre/docs`.
- Task artifacts stay in `tasks/`.
- Shared/local doc boundaries must stay explicit during rollout.

## Current Direction

- Single path: `git submodule`.
- Reliability controls: SOP + Agent Skill + CI guards.
- `git subtree` is out of this task scope to avoid dual-operation drift.

## Why This Changed

The previous read-only mirror fan-out design was judged brittle and operationally noisy. This task now centers on Git-native distribution with stricter operating discipline.

## Entry Files

- `00-phase-map.md`
- `10-phase-0-classification-gate.md`
- `11-phase-0-core-py-docs-classification.md`
- `20-phase-1-source-boundary.md`
- `30-phase-2-strategy-decision.md`
- `31-phase-1-3-execution-output.md`
- `40-phase-3-submodule-reliability-pack.md`
- `50-phase-4-core-py-pilot.md`
- `51-phase-4-execution-output.md`
- `60-phase-5-mixed-doc-split-gate.md`
- `61-phase-5-split-matrix.md`
- `62-phase-5a-execution-output.md`
- `63-phase-5b-execution-output.md`
- `90-review-checklist.md`

## Immediate Next Step

Proceed with the final gated split only after confirming which shared slices of `info-base-ingestion` truly survive the shared-admission gate.
