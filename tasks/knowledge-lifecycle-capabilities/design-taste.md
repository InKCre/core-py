# Design Taste and Discussion Filter

> Active working-memory control，not durable product/technical truth。Canonical common-pattern descriptions remain in
> [documentation promotion](documentation-promotion.md)；this file keeps the small set needed before proposing architecture or
> asking Sir for a decision。

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

## Current Failure Reference

Mail ordinary collection had already persisted valid graph facts。Making a failed `mark_as_seen` attempt block the mailbox
checkpoint would repeatedly re-fetch the delta、possibly pin progress on a permanent external error and couple collection
authority to a workflow convenience。The isolated harm—one message remains unseen and the Job reports a diagnostic—is cheaper
and recoverable。This was a dominated proposal and should never have been escalated as a product decision。

## Scope Discipline

- Unit-specific anti-patterns stay in the owning unit packet；do not promote them merely because they occurred once。
- Common-pattern candidates remain non-durable until implementation evidence passes the promotion test。
- This filter guides discussion；it does not turn taste into validation rules or prohibit evidence-backed exceptions。
