# Meta: `core-py` Post-Split Cleanup

## Status

Exploration (Mode A).

## Intent

Decide what `core-py` still needs after the mixed-doc split is complete under the v9.3 model, without recreating centralized mixed docs by habit.

## Core Question

Under v9.3, what belongs in:

- local `AGENTS.md` as tactical hazard memory
- `docs/30-unit-tdd/` as slow-moving logical unit architecture
- local `docs/00-meta/` as unit-specific workflow/SOP overrides, if any

And what should remain absent because the shared baseline under `docs/_shared/00-meta/` is already enough?

## Working Thesis

Do **not** assume either of these extremes:

- "`docs/30-unit-tdd/` is forbidden"
- "`docs/30-unit-tdd/` must now be created immediately"

The default post-split path should be:

1. separate tactical hazards from slow-moving structure
2. upgrade weak local guides
3. admit a small `docs/30-unit-tdd/` only if a real structural truth survives that separation
4. add local `docs/00-meta/` only if `core-py` has unit-specific workflow pain not solved by the shared baseline

## Entry Files

- `00-phase-map.md`
- `05-v9-3-impact.md`
- `10-unit-tdd-admission-gate.md`
- `11-local-context-coverage-snapshot.md`
- `12-structural-candidate-scan.md`
- `20-cleanup-sequence.md`
- `90-review-checklist.md`

## Immediate Next Step

Use v9.3 to re-evaluate three things in order:

1. which `core-py` subtrees still lack strong tactical local guides
2. whether `core-py` now has slow-moving structural truths worth a minimal `docs/30-unit-tdd/`
3. whether `core-py` needs any local `docs/00-meta/` beyond the shared baseline under `docs/_shared/00-meta/`

Current exploration result:

- tactical gaps are confirmed in `source/`, `sink/`, `resolver/`, and `storage/`
- one real structural candidate has emerged: the `extension -> source/resolver -> info_base -> sink` authority pipeline
