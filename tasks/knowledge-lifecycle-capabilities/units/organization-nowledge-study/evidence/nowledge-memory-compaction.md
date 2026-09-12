# Evidence: Nowledge Memory Compaction

- **Question served**: What concrete use loss does Nowledge Memory Compaction address，what distinctions does it make among
  duplicate、related and evolving information，and what—if anything—transfers to automatic InKCre Organization？
- **Consumer**: [Product design](../product-design.md#memory-compaction--initial-product-inquiry)。
- **Evidence horizon**: Nowledge official documentation/API observed 2026-09-02。Recheck before version-sensitive Product or
  Technical claims。

## Official Evidence

- Memory Compaction is a scheduled weekly task when enabled。It reviews redundant Memories and consolidates confirmed
  duplicates；Nowledge classifies Memory Compaction and Label Consolidation as merge-capable tasks that act after review and are
  off by default。Source：[Background Intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence)。
- The compaction trigger is described as scanning Memories that cover the same topic and suggesting either merging duplicates or
  linking related items。Source：[Trigger Memory Compaction](https://mem.nowledge.co/zh/docs/api/agent/trigger/memory-compaction/post)。
- The plan endpoint previews the exact pre-computed candidate context without asking the Agent to decide、creating EVOLVES
  edges/Crystals or enqueueing work。It offers an optional expensive recent-duplicate probe and bounded candidate limit。Source：
  [Plan Memory Compaction](https://mem.nowledge.co/docs/api/agent/trigger/memory-compaction/plan/get)。
- Nowledge's search guide says compaction can create links、summaries or review items for clusters of similar/redundant Memories，
  and does not silently delete saved Memory text。Source：[Search & Relevance](https://mem.nowledge.co/docs/search-relevance)。

## Evidence Versus Inference

| Evidence / observation | Current inference | Missing evidence / confidence |
| --- | --- | --- |
| Candidate planning is separated from Agent judgment and graph writes。 | Similarity/cluster membership proposes attention；it is not merge authority。 | High。 |
| A candidate may be merged or linked，and compaction may instead produce a summary/review item。 | “Redundancy” is not one semantic relation or one mutation；the operation performs relationship triage。 | High direction；exact classifier contract unknown。 |
| Merge-capable tasks act after review and never silently delete source text。 | Nowledge treats false-positive merge as materially different from safe score/type maintenance。 | High as product boundary；exact retained graph shape unknown。 |
| The feature is Memory-scoped and assumes standalone personal takeaways。 | InKCre cannot equate similar source records、equivalent propositions and duplicate information units merely because their text overlaps。 | High product difference。 |

## Existing InKCre Boundary

- Shared Product truth states that exact source evidence outranks heuristic duplicate reduction。
- Source reconciliation uses the strongest stable external identity；without it，duplication or explicit discard is preferable to
  fuzzy overwrite。
- Blocks/Relations retain information authority while retrieval ranking and representative selection are application
  projections。Therefore search-result crowding alone does not automatically justify destructive Organization mutation。

## Active Inquiry

The current inquiry tests whether the transferable learning is a **redundancy relationship triage** rather than generic merge：

```text
similarity / graph proximity
  -> bounded candidate
     -> determine what is actually shared
        |-> same source-native identity / replay        # Collection reconciliation
        |-> duplicated assertion from one provenance    # possible duplicate relation/merge
        |-> equivalent claim from independent evidence  # preserve source multiplicity
        |-> partial overlap / complementary content     # linking or synthesis
        `-> temporal or epistemic change                # evolution
```

Query-time representative selection cannot stop same-provenance copies from being counted as independent evidence by later
Organization or graph consumers。The current candidate therefore adds a provenance-aware duplicate-assertion Relation while
retaining every Block and source edge。That Relation could let evidence operations count one assertion occurrence，while query
independently derives one representative and graph traversal preserves access to every record/context。

D-480 accepts that non-destructive return。Exact relation contract、candidate trigger、Agent judgment context and consumer
projection remain unapproved；Memory Compaction is closed for this study。
