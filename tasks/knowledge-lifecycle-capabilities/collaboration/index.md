# Collaboration Protocol

> Task-local operating agreement for `knowledge-lifecycle-capabilities`. It coordinates Human/Agent work; it is not
> Product or Technical truth and does not replace repository or organization instructions.

## Roles

Sir owns product intent、material taste/trade-offs、acceptance horizon and authorization for source/durable mutation，commit
and merge。Sir's project knowledge is high-confidence evidence，not an infallible technical authority。

The Agent owns evidence recovery、repository and protocol research、a coherent recommended design、derivation of natural
consequences、preflight、implementation after approval and claim-relative verification。The Agent must not turn Sir into the
author of a solution that can be established from available evidence。

Terminology、material Product/Technical boundaries and acceptance are jointly reconciled。A correction changes the relevant
system model and decision criterion，not only the cited example。

All parallel Unit sessions are peers；there is no coordinator role and no cross-session communication protocol。The roster
provides shared visibility only。When placement、range or authoritative surfaces conflict，the affected session pauses and
reports the conflict to Sir；Sir owns any required coordination or sequencing decision。

## Unit Loop

```text
recover current model
  → Product
  → Technical ↔ Acceptance ↔ implementation-plan probe
  → preflight / spike / branch simulation
  → frozen Acceptance + Execution baseline
  → Impact Handshake
  → Sir explicitly says “开始”
  → Execute
  → Verify / Promote
  → Close
```

- Exploration、research、history inspection、experiments、spikes and task-packet maintenance do not require `开始`。
- `开始` authorizes the reviewed source/durable state diff and its verification，not unresolved investigation。
- A preflight finding that changes Product、owner、public contract or Acceptance returns to that gate。
- Commit、push、merge and cross-owner publication keep their own authorization and governance boundaries。
- A Unit is an implementation responsibility boundary，not a release、repository or folder boundary。

## Discussion Loop

The unit of progress is a more coherent current system model，not another answered question。

1. Recover accepted terms、decisions、code facts and current packet state before proposing a new model。
2. Reconcile the latest input with authority、scope/cardinality、lifecycle and existing contracts。
3. Investigate missing factual or feasibility evidence autonomously。
4. Derive low-risk consequences and remove dominated options。
5. Present at most one surviving material Human fork，with evidence、recommendation、alternative and consequences。
6. Write accepted conclusions and still-open pressure back to the unit packet immediately。
7. Do not reopen accepted decisions merely because context was compacted or implementation has not started。

“一次尽可能只问一个问题” is a ceiling on simultaneous Human review，not an instruction to manufacture one question per
turn。When one coherent answer follows from accepted constraints，the Agent records it and continues。

## Reasoning Instruments

- Start from real InKCre concepts and use cases；do not import an external architecture vocabulary without demonstrated
  pressure。
- Calibrate names as existing project terms、accepted new terms、external protocol terms、temporary discussion language or
  withdrawn inventions。
- For cross-owner changes，draw a small topology before designing the interface。
- For scheduled、async、concurrent、partial or state-dependent behavior，simulate at least two executions and identify the
  persisted fact that changes the second execution。
- For each new parameter，trace who chooses it、its variation grain、authority and consumer。
- Evaluate a public API from caller understanding and misuse resistance；a deep interface is clear，not merely narrow。
- Compare marginal utility、harm、detectability、recovery topology、dependency and obscurity before adding machinery。
- Prefer existing project mechanisms、standard/platform behavior and mature dependencies before custom abstraction。
- Keep Acceptance focused on valuable observable invariants，not incidental identity、order、algorithm or fixture output。

The detailed experimental filters remain in [design taste](../design-taste.md)。

## Verification Allocation

- Static mechanisms own shape、typing、registration and mechanically enforceable structure。
- Runtime evidence is black-box-first through real transport、persistence and realistic data or a credible protocol double。
- Manual/script journeys precede automated regression admission；new automation still requires the task's accepted policy。
- Acceptance does not reshape production code to make a fixture convenient。

## Working-Memory Discipline

- The program packet routes；the active unit packet owns its phase、current model and next pressure。
- Accepted decisions live once in the task decision register；unit files reference them。
- Unstable durable-doc pressure remains task-local until implementation evidence supports promotion to the correct owner。
- Packet write-back occurs during discussion；durable docs are reconciled with implementation，not edited speculatively
  during discussion。
