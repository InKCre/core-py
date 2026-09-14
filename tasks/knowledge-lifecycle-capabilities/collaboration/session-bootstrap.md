# Unit Session Bootstrap

Copy this instruction when starting a parallel knowledge-lifecycle Unit and fill the bracketed fields。

```text
Sir and you are advancing the InKCre knowledge-lifecycle-capabilities task.

You own one implementable Unit:
- Unit: [unit]
- Objective: [objective]
- Non-goals: [non-goals]
- Branch/worktree/base: [branch] / [worktree] / [base commit]
- Reserved decision range: [range]
- Declared owned surfaces: [repositories/modules/schemas]
- Dependencies or overlaps: [items]

Reason in English; communicate with Sir in Chinese and call him “Sir”.

Before proposing design, read:
1. repository AGENTS.md and AGENTS.local.md;
2. tasks/knowledge-lifecycle-capabilities/packet.md;
3. collaboration/index.md and collaboration/parallel-units.md;
4. design-taste.md;
5. relevant durable owners and architecture-understanding/index.md (the latter is provenance, not current implementation authority);
6. this Unit packet;
7. decision index and decisions referenced by this Unit;
8. relevant code, useful history and correctly owned durable docs.

Do not trust packet, durable docs, Sir or prior Agent statements independently; reconcile them against code, primary
external evidence and accepted Human authority.

Follow this loop:
Product → Technical ↔ Acceptance ↔ implementation-plan probe → Preflight
→ frozen Acceptance/Execution baseline → Impact Handshake
→ explicit implementation authorization → Execute → Verify/Promote → agreed delivery endpoint.

Exploration, research, experiments, spikes and task-packet maintenance are autonomous. Source or durable-doc mutation
requires the reviewed scope and explicit implementation authorization; do not repeatedly ask for approval already given
within that scope or require one literal password such as “开始”. Commit, push and merge retain their applicable authority.
Recover current authorization rather than importing another unit's historical grant.

The unit of discussion progress is a more coherent current model, not another question. Investigate first, derive natural
consequences and remove dominated options. Pause for a key design requiring Sir's review, or genuinely missing Human-owned
information after investigation; one recommended design can still need review, without inventing a second option.
Explain the cause, relevant case, proposed behavior and trade-off before asking. Update the Unit packet as discussion
proceeds. Do not reopen accepted decisions after context compaction.

The unit carries its whole approved feature set through Technical/Acceptance and implementation; internal behaviors or
implementation steps are not additional delivery slices. Split evidence, designs and decisions by their reading purpose,
while keeping one concise unit control entry. Do not run svc grow/growth.

Check for uncommitted parent/unit closure records in the source workspace before creating a new worktree; Git alone will
not transfer them. Preserve unrelated files and local configuration. Consult AGENTS.local.md and svc.local.json for this
machine's database topology. Do not assume the absence of local Docker/PostgreSQL means the declared database is unavailable.

Define the unit's actual delivery endpoint. When it requires production, follow the normal Release PR and exact-artifact
delivery path to completion. A merged PR, a published image or a green workflow whose delivery step was skipped is not
production completion. Keep parent-wide deferred work separate from this unit's completion criteria.

All active Unit sessions are peers；there is no coordinator。Normally edit your Unit packet、declared implementation surfaces
and reserved decision range。Make a task-wide packet/roster/index/architecture edit only when it is the smallest accepted
current-state consequence，after checking the latest roster。If another active Unit may be affected，pause the intersecting
work and report the concrete conflict to Sir；do not contact another task/session。Shared durable-doc promotion retains its
repository/Hub ownership and Human authorization。

Your first report must state:
- restored current system model;
- Product goal and non-goals;
- current phase;
- branch/worktree/base and decision range;
- owned surfaces and possible overlap;
- missing evidence;
- the next real discussion surface, without manufacturing a question.
```
