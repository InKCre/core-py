# Design Taste and Discussion Filter

> **Status: experimental，task-wide，not law.** This is active working-memory control，not durable product/technical truth。
> Sir will judge and revise it through actual discussion experience。Canonical common-pattern descriptions remain in
> [documentation promotion](documentation-promotion.md)；this file keeps the small set needed before proposing architecture or
> asking Sir for a decision。

## Experimental Discussion Model

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
5. if one coherent answer remains，record/present the derived result without asking。Only surviving credible forks enter human
   review，one at a time。

This workflow is deliberately experimental。Topology and sequence models are tools selected when they expose the relevant
dependency or time behavior，not compulsory diagram artifacts for every small naming or mechanical decision。

## Before Escalating a Design Question

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

A human decision question is justified only when at least two **credible、non-dominated** answers remain after those filters，
and choosing among them materially changes observable product behavior、authority、public contract、irreversible effects or a
high-cost failure/recovery path。Missing evidence should trigger exploration，not a speculative choice。

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

## Scope Discipline

- Unit-specific anti-patterns stay in the owning unit packet；do not promote them merely because they occurred once。
- Common-pattern candidates remain non-durable until implementation evidence passes the promotion test。
- This filter guides discussion；it does not turn taste into validation rules or prohibit evidence-backed exceptions。
