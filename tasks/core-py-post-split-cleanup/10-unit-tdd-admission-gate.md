# Unit-TDD Admission Gate

## Default Position

Under v9.3, `docs/30-unit-tdd/` becomes a valid layer again.

But validity is not the same as inevitability.

`core-py` should not create `docs/30-unit-tdd/` by reflex. It should create it only if a slow-moving structural truth actually exists and survives the locality test.

## A Unit-TDD Candidate Is Admissible Only If

1. the truth is unit-local rather than product-shared
2. the truth describes slow-moving logical structure rather than local tactical hazards
3. it spans multiple subtrees or survives directory refactors, so no single local `AGENTS.md` is the natural home
4. duplicating it across local guides would reduce readability or create drift
5. code/tests/CI cannot cheaply preserve or communicate it alone
6. the truth is stable enough that it is not just temporary migration reasoning

If any gate fails, the answer is "strengthen local guides instead".

## Non-Admissions

Do not use `docs/30-unit-tdd/` for:

- local tripwires, failure semantics, or write-path hazards that belong in local `AGENTS.md`
- runtime/deployment topology that belongs in `docs/40-deployment/`
- product/shared contracts that belong in `docs/_shared/20-product-tdd/`
- temporary cleanup notes that belong in `tasks/`
- high-level directory summaries that only mirror the code tree without preserving real structural truth

## Current Working Judgment

Current evidence still shows real **local-guide coverage gaps**.

But under v9.3, that is no longer enough to conclude "no unit-tdd".

The correct next move is:

1. strengthen tactical local guides
2. scan for any residual slow-moving architectural truths inside `core-py`
3. only then decide whether a minimal `docs/30-unit-tdd/` should exist
