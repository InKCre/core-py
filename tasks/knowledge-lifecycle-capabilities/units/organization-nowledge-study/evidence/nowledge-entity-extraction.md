# Evidence: Nowledge Entity / Relationship Extraction

- **Question served**: What use loss、trigger、operation and graph result does Nowledge automatic entity/relationship extraction
  own，and is it a new Organization pattern or a composition of breakdown and linking？
- **Consumer**: [Product design](../product-design.md#entity--relationship-extraction--initial-product-inquiry)。
- **Evidence horizon**: Nowledge official documentation/API observed 2026-09-01。Recheck before version-sensitive Product or
  Technical claims。

## Official Evidence

- Background Intelligence runs entity extraction automatically after new Memories arrive，alongside EVOLVES detection。It is an
  independently configurable background task and requires a model for reasoning。Source：
  [Background Intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence)。
- The Knowledge Extraction API describes previewing extraction for one Memory and applying extracted entities/relationships to
  the knowledge graph。Apply records extraction metadata on the Memory。Source：[API reference](https://mem.nowledge.co/docs/api)。
- Preview uses an LLM without writing，returns candidate entities/relationships、one extraction confidence、counts and a write
  plan；apply separately writes supplied entities/relationships and extraction confidence。Sources：
  [Preview KG Extraction](https://mem.nowledge.co/docs/api/memories/memory_id/extract-kg/preview/post)、
  [Apply KG Extraction](https://mem.nowledge.co/docs/api/memories/memory_id/extract-kg/apply/post)。
- Nowledge describes extracted graph content as entities such as people、concepts、technologies and projects，plus relationships
  among them。Source：[See Your Expertise](https://mem.nowledge.co/docs/use-cases/expertise-graph)。
- Search can use shared entities to surface Memories even when their text/labels differ；communities and graph expansion also
  consume the entity graph。Source：[Search & Relevance](https://mem.nowledge.co/docs/search-relevance)。
- Graph search results expose Entity nodes with `entity_type` and confidence metadata；the API separates Entity nodes from
  Memory、Source、Thread and other graph node types。Sources：[Search Graph](https://mem.nowledge.co/docs/api/graph/search/get)、
  [Graph Overview](https://mem.nowledge.co/docs/api/graph/overview/get)。

## Evidence Versus Inference

| Evidence / observation | Current inference | Missing evidence / confidence |
| --- | --- | --- |
| New Memory triggers entity/relationship extraction。 | This is automatic post-persistence Organization in Nowledge，not query-time indexing alone。 | High。 |
| Apply writes Entity/relationship graph data。 | Implicit prose meaning becomes explicit reusable graph information。 | High；exact identity/reuse algorithm unknown。 |
| Preview and apply are separate，but preview exposes one aggregate extraction confidence。 | LLM output is treated as a proposed write；one aggregate score cannot establish every identity and relation independently。 | High separation；per-candidate admission unknown。 |
| Entity-mediated search and communities consume the graph。 | Intended value includes cross-document discovery/navigation rather than graph appearance。 | High。 |
| Nowledge has a first-class Entity node model。 | Its implementation shape cannot transfer by analogy into Block/Relation-only InKCre authority。 | High boundary。 |

## Return

D-479 accepts a narrow transfer：resolve a mention to **existing identity-bearing information** and add source-grounded links；
ambiguity may stay unresolved。Mention recognition、referent resolution、source-to-referent linking、new-anchor materialization
and relation assertion remain separate responsibilities。Automatically creating new identity-bearing information is valuable in
principle but deferred because no credible extraction/identity-establishment pattern was found；a label-only Entity is not
presumed to be InKCre information。

Ontology/domain vocabulary is explicitly excluded by D-478。No Entity type model、automatic extraction behavior or persistence
surface is approved。
