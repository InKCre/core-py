# Evidence: Nowledge Automatic Labeling

- **Question served**: What durable use distinction does Nowledge automatic labeling create，and does it transfer as an
  independent InKCre Organization behavior rather than retrieval projection or contextual linking？
- **Consumer**: [Product design](../product-design.md#automatic-labeling--initial-product-inquiry)。
- **Evidence horizon**: Nowledge official documentation/API observed 2026-09-03。Recheck before version-sensitive Product or
  Technical claims。

## Official Evidence

- Nowledge describes Labels as categories for filtering and organization。New Memories receive 2–4 content-based Labels，and
  existing Labels are reused when they fit；users may edit or add them。Source：[Memories](https://mem.nowledge.co/docs/memories)。
- Search gives a relevance boost when a query matches an assigned Label。Nowledge says this lets the user's own organizational
  structure influence results。Source：[Search Architecture](https://mem.nowledge.co/docs/concepts/search-architecture)。
- Label assignment is represented separately from Memory content；the API exposes Label records plus assignment/removal for
  Memories and Sources。Source：[API Reference](https://mem.nowledge.co/docs/api)。
- Label consolidation has a dry-run path combining deterministic canonical-fork planning with model-judged semantic and
  cross-language pairs。Semantic similarity is explicitly only a candidate signal；apply atomically moves assignments and
  removes the source Label after checking the preview plan。Sources：[Preview Label Consolidation](https://mem.nowledge.co/zh/docs/api/labels/consolidation-preview/post)、
  [Label Merge Candidates](https://mem.nowledge.co/docs/api/labels/merge-candidates/get)、
  [Apply Label Merge](https://mem.nowledge.co/docs/api/labels/label_id/merge/apply/post)。

## Evidence Versus Inference

| Evidence / observation | Current inference | Missing evidence / confidence |
| --- | --- | --- |
| A Label is a category/filter and search-match boost。 | Nowledge combines persistent grouping with an application-side ranking signal。 | High。 |
| Automatic assignment emits 2–4 Labels and prefers existing ones。 | Fixed count and naming convention are Product heuristics；reuse tries to avoid fragmented grouping vocabulary。 | High behavior；admission logic unknown。 |
| Labels attach to both Memories and Sources。 | Label meaning is intentionally broader than one Entity or Memory type，but its semantic role is not explicit。 | High observation；exact graph semantics unknown。 |
| Consolidation distinguishes canonical forks from model-judged near synonyms and supports preview/apply。 | Label-string similarity is not identity authority；consolidation has the same candidate/judgment separation already accepted elsewhere。 | High。 |

## Return

D-482 separates three meanings hidden under one Label feature：

```text
label-like output
  |-> lexical recall cue only                         # application/search projection
  |-> membership/context assertion to existing info  # existing-referent contextual linking
  `-> newly materialized named category               # new-anchor materialization
```

The first does not modify info-base meaning；the second is already covered by D-476/D-479；the third inherits the unresolved
identity/admission problem that deferred new Entity materialization。No distinct Product meaning remains，so Automatic Labeling
is closed with no independent transfer。No Label node/field、fixed label count、naming convention、automatic assignment or
consolidation behavior is approved。
