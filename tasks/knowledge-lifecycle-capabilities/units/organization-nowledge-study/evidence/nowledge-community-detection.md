# Evidence: Nowledge Community Detection / Graph Analysis

- **Question served**: Does a structural graph cluster become durable semantic Organization，or remain a model-relative
  projection/candidate mechanism？
- **Consumer**: [Community Detection Product shard](../product/community-detection.md)。
- **Evidence horizon**: Nowledge official documentation/API observed 2026-09-04。Recheck before version-sensitive Product or
  Technical claims。

## Official Evidence

- The Graph Compute action runs Louvain community detection and colors the graph by cluster；the same graph experience exposes
  centrality、bridge entities、community summaries and member counts。Source：
  [Knowledge Graph](https://mem.nowledge.co/docs/knowledge-graph)。
- Community search uses clusters of strongly connected entities to surface Memories that direct keyword/semantic matches might
  miss。Source：[Search architecture](https://mem.nowledge.co/docs/concepts/search-architecture)。
- Community detection runs periodically and rebuilds the Entity graph's community structure for community-based search。It is
  described as a direct-function task rather than an LLM task。Source：
  [Background intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence)。
- Wiki topic clustering groups knowledge into topics and gives each a name；the topic pages are derived rather than stored and
  refresh from underlying graph data。Source：[LLM Wiki](https://mem.nowledge.co/docs/concepts/llm-wiki)。
- The API exposes graph analysis/community/centrality operations separately from List Communities and Community Details with AI
  summaries，indicating separate structural-analysis and presentation surfaces。Source：
  [API Reference](https://mem.nowledge.co/docs/api)。
- Nowledge documents communities as computed by Louvain over the global Entity projection。Related-community strength is the
  count of cross-community Entity `RELATES_TO` edges and is not meaningful under a single-Space lens。Source：
  [Get Related Communities](https://mem.nowledge.co/docs/api/library/community/community_id/related/get)。
- Graph search returns algorithm、resolution、membership、community hulls、PageRank and other visualization metadata alongside
  underlying nodes and edges。Source：[Search Graph](https://mem.nowledge.co/docs/api/graph/search/get)。

## Evidence Versus Inference

| Evidence / observation | Current inference | Missing evidence / confidence |
| --- | --- | --- |
| Louvain computes communities from a selected Entity graph projection。 | Membership is algorithm/projection-relative derived support，not an intrinsic semantic fact。 | High。 |
| Communities color the graph and support browse/search expansion。 | Their primary direct value is Application/use projection。 | High。 |
| Community detection and AI summaries are exposed as separable capabilities。 | Structural clustering need not acquire semantic authority merely because an LLM names it。 | High。 |
| Wiki topic pages are derived rather than stored。 | A live community summary may remain a presentation projection without creating a durable information node。 | High。 |
| Community results expose entities/sample memories and support Agent analysis。 | A cluster can seed semantic exploration or n-ary synthesis candidate formation。 | High。 |
| Related-community strength counts `RELATES_TO` edges。 | Results depend on which relation meanings are admitted/weighted；generic graph connectedness does not prove topical relation。 | High conceptual confidence；exact Nowledge projection rules are only partially documented。 |
| Louvain returns a partition for one projection。 | One membership lens must not become an exclusive ontology for information that participates in overlapping subjects/models。 | High conceptual confidence。 |

## Product Disposition

D-491 finds no independent Community Detection Organization method。Community membership、centrality、bridges and
topic-coloring remain rebuildable graph-analysis/Application projections。They may seed a D-493-classified graph-guided
candidate heuristic，
but an exact Organization behavior must independently judge whether linking、synthesis、evolution or no-op follows。

An independently reusable thematic explanation may route to D-472 provenance-preserving n-ary synthesis；an ephemeral name or
live Wiki summary does not need graph persistence。No algorithm、projection、community entity or schedule is transferred。
