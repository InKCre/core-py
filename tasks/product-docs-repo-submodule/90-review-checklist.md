# Review Checklist

## Architecture

- Is transport separated from ownership classification?
- Is submodule default justified by explicit criteria rather than habit?
- Is subtree explicitly out of scope for this task to avoid dual-operation drift?

## Reliability

- Does SOP explicitly enforce "push source first, then pointer update"?
- Does Agent Skill prevent detached-HEAD edits and unsafe pointer bumps?
- Do CI checks catch invalid pointers and path collisions?

## Scope Hygiene

- Are we avoiding new durable-doc changes in this task phase?
- Is task documentation compact and non-duplicative?
- Is `00-meta` present as the task entry anchor?

## Pilot Readiness

- Is the first rollout batch small and reversible?
- Are rollback steps explicit and fast?
- Are unresolved mixed files excluded from pilot?

## Phase 5 Split Hygiene

- Does each moved statement pass the shared-admission gate?
- Are local containers upgraded before extracting local implementation details?
- Are we avoiding shared docs that depend on `core-py`-only class or method names?
- Are empty mixed docs deleted only after inbound links are updated?
