# Parallel Peer Sessions

Parallelism changes work placement，not the Unit loop or mutation gates。

## Topology

```text
shared task packet / roster / decision register
  ├─ peer unit session / feature branch / worktree
  ├─ peer unit session / feature branch / worktree
  └─ peer unit session / feature branch / worktree
```

Each session advances at most one active Unit。The program may have multiple active Units only when their ownership、decision
and integration surfaces are explicit in the [roster](roster.md)。

## Peer Authority

All Unit sessions are peers。No session is a program coordinator or standing integration authority。The program packet、roster
and decision register are shared task control，not the property of one role。

Each peer may make the smallest necessary task-wide control edit for its own declared placement、accepted decision navigation、
cross-unit consequence or post-merge state。Before doing so it reads the latest roster and shared surface and preserves
unrelated peer work。If the edit would change another active Unit's owned surface or approved baseline，the session pauses and
reports that overlap to Sir；it does not contact the other session directly。

## Unit-Session Ownership

One unit session owns：

- its exact `units/<unit>/**` control surface；
- its declared feature branch、worktree and base commit；
- only its reserved decision range/shards；
- its Product-through-Verify loop、PR and acceptance evidence；
- changes inside the declared implementation surface after the normal `开始` gate。

A unit session records cross-unit/common-pattern candidates in its own packet。It may promote an accepted task-wide control
consequence itself when no active peer owns an intersecting surface；otherwise it pauses and reports the intersection to Sir。
Shared durable-doc publication still follows its repository/Hub ownership and Human authorization，not peer status。

## Collision Rules

- Product research、external protocol research and preflight may usually proceed in parallel。
- Two implementations do not concurrently own the same schema/migration baseline、shared Manager/runtime、extension
  lifecycle、AI/Agent runtime、shared UI package or durable owner。Assign one owner or extract and serialize a prerequisite。
- A unit may read another branch's proposal，but unmerged branch state is not shared authority。
- Before Execute，rebase or otherwise reconcile the unit with current `main` and repeat address-sensitive preflight。
- Multi-repo branches use one unit slug where practical，while Hub、Spoke、shared-ref and release commits retain their
  separate owner/order constraints。
- A unit PR is the implementation integration boundary。The owning peer updates program state and decision navigation with a
  narrow current-state patch when that update becomes true；other peers do not need a central session to relay it。

## Decision Allocation

The decision register remains one task authority。Before writing a new decision，a peer claims a non-overlapping numeric range
in the latest roster and checks the decision directory for collision。The peer writes only files wholly inside that range and
may add its own narrow `decisions/index.md` navigation/current-edge update。

If a range becomes insufficient，the peer claims another currently unused range in the roster before writing it。If concurrent
claims collide，the later-integrated peer moves its unmerged decisions to a free range。Unused IDs may remain unused；monotonic
history is more valuable than compact numbering。

## Conflict Escalation

Pause the affected design or implementation when：

- another active unit owns the same authoritative surface；
- a local conclusion would change a task-wide term、common pattern or accepted decision；
- a shared prerequisite changes another unit's approved baseline；
- durable ownership crosses Hub/Spoke boundaries and the publication order is not already established。

Do not contact another task/session。Pause only the intersecting work and present the concrete ownership、ordering、baseline or
Product fork to Sir。Sir decides whether work is serialized、reassigned or allowed to proceed；do not create a coordinator or
relay role as an intermediary。
