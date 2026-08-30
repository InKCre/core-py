# Parallel Unit Coordination

Parallelism changes work placement，not the Unit loop or mutation gates。

## Topology

```text
program coordinator session
  ├─ unit session / feature branch / worktree
  ├─ unit session / feature branch / worktree
  └─ unit session / feature branch / worktree
```

Each session advances at most one active Unit。The program may have multiple active Units only when their ownership、decision
and integration surfaces are explicit in the [roster](roster.md)。

## Coordinator Ownership

Only the coordinator normally edits：

- the program packet and active-unit roster；
- capability map and task-wide design taste；
- cross-unit architecture understanding；
- decision-range allocation and decision index；
- task-wide durable-doc promotion routing；
- shared-core overlap、dependency ordering and post-merge program closure。

## Unit-Session Ownership

One unit session owns：

- its exact `units/<unit>/**` control surface；
- its declared feature branch、worktree and base commit；
- only its reserved decision range/shards；
- its Product-through-Verify loop、PR and acceptance evidence；
- changes inside the declared implementation surface after the normal `开始` gate。

A unit session records cross-unit/common-pattern candidates in its own packet and reports them to the coordinator。It does
not independently promote them into task-wide control or shared durable docs。

## Collision Rules

- Product research、external protocol research and preflight may usually proceed in parallel。
- Two implementations do not concurrently own the same schema/migration baseline、shared Manager/runtime、extension
  lifecycle、AI/Agent runtime、shared UI package or durable owner。Assign one owner or extract and serialize a prerequisite。
- A unit may read another branch's proposal，but unmerged branch state is not shared authority。
- Before Execute，rebase or otherwise reconcile the unit with current `main` and repeat address-sensitive preflight。
- Multi-repo branches use one unit slug where practical，while Hub、Spoke、shared-ref and release commits retain their
  separate owner/order constraints。
- A unit PR is the integration boundary。The coordinator updates program state and decision navigation after merge rather
  than making every parallel branch edit the same index files。

## Decision Allocation

The decision register remains one task authority。Before a unit session writes a new decision，the coordinator reserves a
non-overlapping numeric range in the roster。The unit writes only files wholly inside that range and does not edit
`decisions/index.md`；the coordinator adds navigation when integrating the unit。

If a range becomes insufficient，the session requests another range instead of taking the next global number。Unused IDs may
remain unused；monotonic history is more valuable than compact numbering。

## Escalation to the Coordinator

Pause the affected design or implementation when：

- another active unit owns the same authoritative surface；
- a local conclusion would change a task-wide term、common pattern or accepted decision；
- a shared prerequisite changes another unit's approved baseline；
- durable ownership crosses Hub/Spoke boundaries and the publication order is not already established。

Unrelated work in the same unit may continue；the escalation does not turn the whole session into a generic blocker。
