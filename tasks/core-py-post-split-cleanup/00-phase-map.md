# Phase Map

## Objective

Reach an explicit post-split cleanup decision for `core-py` under v9.3 without regressing back into centralized mixed docs.

## Phase Sequence

### Phase 0: v9.3 Impact Framing

Output:

- explicit list of assumptions that changed from v9.2
- explicit note on shared-baseline mismatch risk

### Phase 1: Tactical Coverage Audit

Output:

- snapshot of local guide quality by subtree
- explicit list of weak or missing local-context anchors

### Phase 2: Structural Candidate Scan

Output:

- candidate list of slow-moving, unit-local architectural truths
- explicit rejection list for truths that should stay local or shared

### Phase 3: Unit-TDD Admission Gate

Output:

- decision rule for whether `docs/30-unit-tdd/` is justified in `core-py`

### Phase 4: Local Guide Upgrade Plan

Output:

- ordered cleanup list for subtrees that still need stronger local `AGENTS.md`
- ordered list of any minimal `docs/30-unit-tdd/` seeds, if admitted

### Phase 5: Meta-Engine Gap Check

Output:

- decision on whether `core-py` needs any local `docs/00-meta/`
- or explicit confirmation that the shared baseline under `docs/_shared/00-meta/` is sufficient for now

### Phase 6: Residual Unit-Local Truth Decision

Output:

- either "no centralized unit-tdd needed"
- or one sharply bounded candidate for `docs/30-unit-tdd/`

## Cross-Phase Invariants

- do not recreate mixed docs under `docs/15-alignment/` or `docs/20-product-tdd/`
- keep local `AGENTS.md` focused on tactical hazards, authority, and tripwires
- use `docs/30-unit-tdd/` only for slow-moving logical unit architecture
- prefer the shared `docs/_shared/00-meta/` baseline unless unit-specific workflow pain is demonstrated
- keep task artifacts compact and decision-oriented
