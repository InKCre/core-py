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
  → explicit implementation authorization
  → Execute
  → Verify / Promote
  → agreed delivery endpoint / Close
```

- Exploration、research、history inspection、experiments、spikes and task-packet maintenance are autonomous。
- 明确的实施授权覆盖已复核方案及必要验证，不要求字面口令“开始”，也不重复索取已经给出的授权。
  新的实质修复方案仍先复核，不能从另一 unit 的历史授权推导当前权限。
- A preflight finding that changes Product、owner、public contract or Acceptance returns to that gate。
- Commit、push、merge and cross-owner publication keep their own authorization and governance boundaries。
- A Unit is an implementation responsibility boundary，not a release、repository or folder boundary。
- 同一 unit 的整组产品功能共同进入技术设计、验收与实现；内部行为和实现步骤不另切 delivery slices。
  按阅读目的拆分设计、证据和决策文件，保留一个简洁的 unit 控制入口，不使用 svc grow/growth。
- 关闭条件以约定的实际交付终点为准。要求生产发布时，PR 合并、镜像上传或绿色但跳过部署的 workflow 都不足以
  关闭 unit；应核对正常发布路径中的版本、实际部署及健康结果。生产交付也不等于所有语义判断正确。

Parallel Unit sessions are peers rather than coordinator/worker roles。Each session owns one Unit and may minimally maintain
the shared program packet、roster and navigation for its own registration or returned result。Orthogonal sessions do not need
routine communication；actual owner overlap、dependency or shared-baseline change is reported to Sir for reconciliation。

## Discussion Loop

The unit of progress is a more coherent current system model，not another answered question。

1. Recover accepted terms、decisions、code facts and current packet state before proposing a new model。
2. Reconcile the latest input with authority、scope/cardinality、lifecycle and existing contracts。
3. Investigate missing factual or feasibility evidence autonomously。
4. Derive low-risk consequences and remove dominated options。
5. 一次呈现一个关键设计复核面，解释证据、案例、因果链、建议及取舍；有真实替代方案才比较，不为提问虚构选项。
6. Write accepted conclusions and still-open pressure back to the unit packet immediately。
7. Do not reopen accepted decisions merely because context was compacted or implementation has not started。

“一次尽可能只问一个问题” is a ceiling on simultaneous Human review，not an instruction to manufacture one question per
turn。When one coherent answer follows from accepted constraints，the Agent records it and continues。
关键的新方案即使只有一个推荐方向，也可能需要 Sir 复核。若自主调查后仍缺少决定方向的信息或思路，应说明
已知事实和具体缺口再请求帮助；不能把“没有第二个方案”当成跳过确认的依据。

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
