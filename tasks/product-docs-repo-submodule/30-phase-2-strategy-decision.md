# Phase 2: Strategy Decision (Lock `submodule`)

## Decision Frame

Lock transport by first principles, not preference:

- consistency of consumed version
- operator error surface
- reviewability
- rollback cost
- CI reproducibility

## Chosen Strategy: `git submodule`

Strengths:

- explicit pinned version per consumer commit
- clear provenance and rollback by pointer
- no content copy in superproject history

Weaknesses:

- detached HEAD confusion
- requires explicit init/update steps
- pointer update discipline required

Mitigation set:

- strict SOP
- Agent Skill enforcement
- CI guardrails

## Explicit Non-Goal For This Task

- do not design or run a parallel `git subtree` flow
- do not maintain dual SOPs in the same execution plan

Rationale:

- dual transport modes increase operator confusion and review ambiguity
- one rollout should validate one mechanism end-to-end

## Decision Gate Questions

- Can the team consistently follow pointer-update SOP in review?
- Do CI/CD and local tooling already support recursive submodule checkout?
- Is detached HEAD confusion controllable with Skill and checks?

## Exit Criteria

- accepted default transport
- accepted non-goal boundary (no subtree in this task)
