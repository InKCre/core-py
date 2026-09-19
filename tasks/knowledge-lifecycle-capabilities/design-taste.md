# Design Taste and Discussion Filter

> **Status: experimental，task-wide，not law.** This is active working-memory control，not durable product/technical truth。
> Sir will judge and revise it through actual discussion experience。Canonical common-pattern descriptions remain in
> [documentation promotion](documentation-promotion/index.md)；this file keeps the small set needed before proposing architecture or
> asking Sir for a decision。

The task's Human/Agent roles、Unit gates、write-back discipline and parallel-session ownership are defined in the
[collaboration protocol](collaboration/index.md)。This file only filters design judgment and question escalation。

## Experimental Discussion Model

Agent Tool 的 task-level 设计原则统一维护于 [Agent Tool common patterns](common-patterns/agent-tools.md)。
涉及工具形态、发现、参数/说明、错误或响应设计时先读该文件；本处不另存一份规则。

涉及 schema 与读写校验位置时，使用 [校验边界指南](common-patterns/validation-boundaries.md)：先定位建立
输入合同的边界，不因函数分层或 typed 返回而反复验证已经持久化的数据。

The unit of progress is a more coherent、evidence-backed current system model，not another answered question or a longer
decision register。Sir's preference to ask one question at a time is an upper bound on simultaneous human review，not a
requirement to manufacture one question after every answer。

Before turning an unresolved point into a human question：

1. reconcile the latest accepted decision with the owning Product/Technical model and derive its natural consequences；
2. classify each proposed value by authority、scope/cardinality and lifecycle。When several owners/lifecycles interact，draw a
   small topology before designing their interfaces；
3. when behavior is recurring、asynchronous、partial or state-dependent，replay at least two executions in a sequence/state
   model and identify the persisted fact that makes the second execution different；
4. eliminate choices already dominated by confirmed constraints and marginal utility；
5. 自然推论可记录后继续；新的关键设计仍需复核，即使只剩一个推荐方向。不为形成问题而制造另一个选项。

This workflow is deliberately experimental。Topology and sequence models are tools selected when they expose the relevant
dependency or time behavior，not compulsory diagram artifacts for every small naming or mechanical decision。

## Before Escalating a Design Question

讨论某一层接口时，复核对象应是该层新增或改变的合同，而不是重新确认其调用领域的既有规则。既有规则用于
内部预演与一致性检查；只有接口方案确实会改变业务行为、产生歧义或暴露冲突时，才展开相关规则供 Sir 审查。
例如 CLI / REST 的评审聚焦命令归属、路径、输入输出和协议语义，不把 Thread 快照等既有生命周期当作新决策。
这是 task-wide experimental discussion guideline，不免除调查、接口文档或实现时保持业务语义的责任。

设计对外操作时，先确认调用者要提交什么、何时算受理，再选择内部执行入口。已有同步方法或 Peer inbound
是可复用实现的证据，不自动决定新接口的生命周期；输入属于哪个领域，也不决定行为归属。D-595 的反例是
从 rumination 接收 Block、已有立即执行门面，推导出 Block 下的同步 CLI 动作。这里应复用任务受理与控制，
不以更少的包装代码换掉调用者需要的 Job 语义；反过来也不把普通记录编辑机械改成 Job。

Run every candidate through these filters first：

1. **Authority and lifecycle**：does the proposal make one owner/progress cursor depend on an orthogonal lifecycle merely
   because the mechanisms are adjacent？If so，separate them unless correctness evidence requires coupling。
2. **Marginal utility**：compare unresolved harm and recovery topology against dependency、obscurity、maintenance and new
   failure modes。Stop when the remaining harm is cheaper than the next mechanism（U-011、U-033、U-037、U-044）。
3. **Deep-module completion**：keep public completion semantics shallow；do not force callers or generic infrastructure to
   understand internal residue、retry、created/existing or domain completeness that they cannot use（U-041、U-042）。
4. **Primary versus orthogonal effects**：do not hold accepted primary progress behind a lower-value best-effort side effect
   when that failure neither invalidates the primary fact nor prevents safe future operation（U-048 candidate）。
5. **Natural consequence**：derive low-risk names、mechanical validation、ordinary error mapping and dominated choices without
   asking Sir to select them。Record the result and expose it at the batch boundary。

需要 Sir 复核的是会实质改变产品行为、authority、公开合同或重要代价的方案，不限于存在两个备选答案的情形。
有真实取舍时提供推荐并解释理由；仅为已确认模型的低风险推论时记录后继续。缺证据先调查，调查后仍需要
Sir 的信息或方向才能推进时，明确缺口，而不是提出无依据的选项。

## Operational and safety reasoning discipline

1. Do not turn ordinary implementation review into a broad safety or security audit。Safety reasoning starts only from a
   specific actor、capability、asset、boundary、harm and attack path confirmed to exist in the current scope。
2. Prefer conventional platform/library controls and their normal verification surfaces。A novel security design or bespoke
   security verification needs a concrete uncovered attack path and demonstrated return。
3. Operational safeguards must preserve observability：record actionable internal context even when the public completion
   semantic is intentionally shallow。
4. Do not escalate an ordinary edge/state race as `fail-fast` or `fail-closed` work for the Human or caller。Reconcile it at
   the owning boundary、return the domain's ordinary completion outcome，or expose a repair action only when the caller can
   meaningfully perform one。

## API / JSON batch outcomes

For a batch of independently executable atoms，prefer one ordered result atom per admitted input：

- retain the natural correlation key and input order；
- let the successful domain payload prove success instead of repeating `status: found`；
- put `error` only on the failed atom，with a small actionable code and observable message；
- do not split successes and failures into parallel arrays or abort siblings merely because one atom failed；
- reserve whole-operation failure for a shared fault that prevents the admitted batch from producing its result。

This is an experimental API/JSON design pattern，not a universal rule。Do not apply it when the batch is semantically atomic，
when one result changes how later inputs must execute，or when partial effect would violate the owning domain contract。

## Current Failure Reference

Mail ordinary collection had already persisted valid graph facts。Making a failed `mark_as_seen` attempt block the mailbox
checkpoint would repeatedly re-fetch the delta、possibly pin progress on a permanent external error and couple collection
authority to a workflow convenience。The isolated harm—one message remains unseen and the Job reports a diagnostic—is cheaper
and recoverable。This was a dominated proposal and should never have been escalated as a product decision。

Media-interpretation routing exposed the deeper discussion failure：after accepting per-modality Agents，the next response
treated “produce another decision question” as progress and mechanically projected modality into Cron/Job parameters。The
existing facts already implied one parameterless convergence Job：Cron owns a static template，Organization derives modality per
candidate，and graph state changes the next candidate set。A topology plus two-occurrence sequence would have made that
implication explicit，but the root correction is to make model reconciliation—not question production—the work unit。

### Do not escalate an unavoidable defect into a universal prerequisite

Another recurring Agent failure shape is：

```text
notice one case where an accepted mechanism cannot provide an absolute guarantee
  -> silently upgrade best-effort Product semantics into a completeness requirement
     -> overlook the accepted repair/degradation path
        -> invent a new global identity、state or infrastructure prerequisite
           -> reopen Product scope and ask Sir to choose among invented machinery
```

The underlying bias is toward logical closure：a universal invariant is easier to reason about than a useful mechanism with an
explicit residual。That neatness is not Product value。It converts an unavoidable or low-observability defect into scope growth，
discards existing recovery topology and makes the Human review a solution to a problem the accepted model did not promise to
eliminate。

Before promoting an imperfection into a prerequisite：

1. recover the already accepted normal path、version/change representation and repair/reapplication law；
2. distinguish a producer violating the preferred path from a limitation that the system cannot observe or control；
3. simulate how the graph reaches a corrected state when the change is observable；
4. state the remaining defect and best-effort boundary without pretending it vanished；
5. add identity/state/infrastructure only if the residual defeats the promised Product value at material frequency or harm。

The Organization synthesis correction is the reference case：ordinary edits should create a new Block plus `edited` Relation；
`synthesis` 关系为可观察的上游变化提供重新综合的路径（D-503 修正了旧名 `contributes to`），不意味着已实现通用
传导引擎。bytes changing behind an unchanged external Storage pointer remain an acknowledged best-effort defect。
That defect does not justify a universal stable-address/version subsystem。

## Scope Discipline

- Unit-specific anti-patterns stay in the owning unit packet；do not promote them merely because they occurred once。
- Common-pattern candidates remain non-durable until implementation evidence passes the promotion test。
- This filter guides discussion；it does not turn taste into validation rules or prohibit evidence-backed exceptions。
