# Review Checklist

## Scope And Ownership

- Have we separated product-scope docs from unit-local docs by actual usage, not by directory name?
- Have we explicitly identified mixed files that need splitting?
- Is there any file still pretending to be product truth while only describing `core-py` internals?

## `.github` Source Design

- Is the source subtree name clear enough?
- Does the source README explain ownership without requiring tribal knowledge?
- Are site/profile concerns cleanly separated from product durable docs?

## Mirror Contract

- Is the mirror policy simple enough for humans and agents to follow?
- Can a mirrored file be recognized immediately?
- Are destination paths stable and collision-free?

## Automation

- Is the sync path deterministic?
- Is there a clear auth story?
- Is PR noise controlled?
- Is failure handling explicit?

## `core-py` Rollout

- Is the first rollout batch intentionally small?
- Are local docs protected?
- Is rollback defined before rollout starts?

## Long-Term Operations

- Can maintainers diagnose drift quickly?
- Can accidental local edits be caught early?
- Is adding a new consumer repo operationally straightforward?
