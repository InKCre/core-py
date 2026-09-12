# Evidence: Nowledge Flags / Memory Maintenance

- **Question served**: Which Flag/maintenance meanings are durable information organization，which are attention/lifecycle
  projections，and does `needs verification` expose an uncovered Product distinction？
- **Consumer**: [Flags / Memory Maintenance Product shard](../product/flags-memory-maintenance.md)。
- **Evidence horizon**: Nowledge official documentation/API observed 2026-09-04。Recheck before version-sensitive Product or
  Technical claims。

## Official Evidence

- Nowledge describes a Flag as a contradiction、stale information or a claim needing verification。Flags appear in the Timeline。
  Source：[Using Nowledge Mem](https://mem.nowledge.co/docs/usage)。
- Its detailed Background Intelligence page defines `Contradiction` as two Memories disagreeing，`Stale` as newer knowledge
  superseding older，and `Needs verification` as a strong claim without corroboration。A user may dismiss、acknowledge or link a
  Flag to a resolution。Source：[Background Intelligence](https://mem.nowledge.co/docs/advanced-features)。
- When a Crystal source is updated、challenged or replaced，Nowledge flags the Crystal as stale and proposes re-evaluation rather
  than silently rewriting it。Source：[Crystals](https://mem.nowledge.co/docs/concepts/crystals)。
- Memory Maintenance prepares a Timeline review when stale or overlapping Memories may add noise。Facts/events may become
  low-risk archive candidates after review；preferences、decisions、plans、procedures、learnings、rules、identities and context are
  not mechanically archived by freshness alone。Source：
  [Memory decay](https://mem.nowledge.co/docs/concepts/memory-decay)。
- Nowledge's Memory lifecycle separates active everyday recall、archived retained history and explicitly removed content。
  Freshness/decay only affects ranking；retiring、forgetting and deletion are explicit actions，and moving aside is reversible。
  Source：[Memory lifecycle](https://mem.nowledge.co/docs/concepts/memory-lifecycle)。
- Applying reviewed cleanup candidates re-reads source-of-truth rows and re-runs classification so a stale UI review cannot
  archive content that was visited、pinned or protected after rendering。Source：
  [Archive Memory Cleanup Candidates](https://mem.nowledge.co/docs/api/agent/trigger/memory-cleanup/archive/post)。
- The semantic-maintenance lane similarly re-reads submitted candidates and only queues rows that still qualify for bounded
  Memory Compaction；it is not an automatic merge。Source：
  [Queue Memory Cleanup Compaction](https://mem.nowledge.co/docs/api/agent/trigger/memory-cleanup/compaction/post)。
- The Feed API separates resolving an action-required event，with optional graph mutations，from soft-deleting the presentation
  event。Source：[API Reference](https://mem.nowledge.co/docs/api)。

## Evidence Versus Inference

| Evidence / observation | Current inference | Missing evidence / confidence |
| --- | --- | --- |
| Contradiction and supersession Flags correspond to documented EVOLVES meanings。 | The durable condition belongs to evidence/evolution Relations；the Flag card is Application display derived from it。 | High。 |
| Crystal stale status follows upstream source changes and proposes re-evaluation。 | This routes to D-473 dependency propagation rather than a generic stale state。 | High。 |
| Dismiss/acknowledge/link-resolution are distinct user actions。 | Attention state must not silently change the underlying semantic condition；exact resolution may create separate graph meaning。 | High conceptual confidence；exact Nowledge mutation payload is not documented here。 |
| Needs verification means strong claim without corroboration。 | This suggests evidence-coverage value but does not define a bounded evidence universe or distinguish not-found from not-processed。 | High uncertainty about semantics；medium-high residual-value confidence。 |
| Maintenance separates low-risk archive candidates from semantic compaction material。 | The feature is routing/presentation over existing lifecycle、ranking and Organization owners，not one semantic behavior。 | High。 |
| Apply APIs revalidate current rows and lane eligibility。 | This is a Nowledge-specific UI/task/lifecycle safeguard；there is no current InKCre review-plan lifecycle from which to infer a transfer。 | High evidence；transfer rejected as premature。 |
| Removed content requires explicit action and archived content remains searchable。 | Cleanup packaging must not authorize automatic info-base deletion or equate default-recall removal with information loss。 | High。 |

## Product Closure

D-492 closes Contradiction、semantic Stale and maintenance routing through accepted owners，while treating Flag
cards as Application display derived from existing graph meaning。It retains `Needs verification` as a genuine but underspecified bounded
evidence-coverage pressure：absence of supporting Relations cannot show whether evidence was searched。

No common Flag state law、Memory lifecycle、cleanup behavior、review-plan revalidation mechanism or Human review state is
transferred。A future evidence-assessment
behavior requires concrete scope、candidate/exploration、coverage witness、freshness and later-use semantics before approval。
