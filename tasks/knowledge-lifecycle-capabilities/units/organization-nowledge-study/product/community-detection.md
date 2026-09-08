# Product Study: Nowledge Community Detection / Graph Analysis

- **State**: closed under D-491；structural projection/candidate use retained，semantic Community authority rejected。
- **Evidence**: [Nowledge Community Detection](../evidence/nowledge-community-detection.md)。
- **Decision authority**: [D-491](../../../decisions/D491-D500.md)。

## Concrete Product Case

Suppose the graph contains deployment、database and incident information。A structural algorithm finds one dense cluster around
PostgreSQL、migration and rollback，then colors it as a “database operations” community。This can improve three later uses：

- a person can browse a bounded topical region instead of the whole graph；
- retrieval can expand from a matching entity into structurally nearby information；
- an Organization behavior can inspect the cluster as a candidate set for linking or synthesis。

But the cluster is not automatically semantic truth。A shared source Block may connect unrelated topics through provenance；a
high-degree generic Entity may join domains that should remain separate；a different relation projection、resolution or time
slice may produce another partition。The useful claim is “these nodes are dense under projection P and algorithm A”，not “these
information units intrinsically form one topic”。

## What Nowledge Does

Nowledge periodically rebuilds communities over its global Entity projection。The Graph UI's Compute action runs Louvain
community detection，colors clusters and exposes community membership、centrality、bridge entities and AI-generated summaries。
Communities feed graph browsing、Wiki topic pages and community-mediated search。Related communities are ranked from the count of
cross-community Entity `RELATES_TO` edges。

The detector is a direct graph function；LLM summarization is a separate capability。Nowledge packages the structural partition、
topic naming、search expansion、visualization and possible later Crystal/report synthesis into one graph experience。

## Structural Projection Is Not Semantic Authority

Community output depends on choices outside the persisted information itself：

```text
authoritative Block / Relation graph
  -> declared analysis projection
     (eligible nodes + eligible Relation meanings + weights + scope + time lens)
  -> algorithm + parameters
  -> rebuildable membership / centrality / bridge metrics
```

Changing any projection or algorithm choice can move a node without changing the source graph。Community IDs and partitions are
therefore model-relative derived support，similar in authority shape to a retrieval index。They should not become intrinsic Block
types、canonical topic membership or a reason to rewrite graph Relations for visual tidiness。

This boundary is especially important in InKCre because Relation semantics are heterogeneous。Provenance、containment、semantic
role、evolution、evidence and ordinary contextual linking do not all mean topical affinity，and a generic connectedness count
cannot decide which ones the analysis should weight。

## One Partition Versus Overlapping Information Properties

Louvain normally produces one partition for the selected graph projection。That is useful computational output，not an ontology。
One information unit may participate in several topics/models/properties，just as one information unit may participate in several
evolution models。A single community assignment must not erase those overlapping semantics。

Different projections may legitimately expose different lenses：subject affinity、source provenance、collaboration structure、
time-bounded activity or evidence topology。The projection name and parameters own the meaning；“community” alone does not。

## Mapping To Existing InKCre Behaviors

| Output | Candidate owner / route | Persistence boundary |
| --- | --- | --- |
| membership、centrality、bridge score | graph-analysis/application projection | rebuildable；not graph authority |
| topic-colored graph and browsing index | Application/view | no graph mutation |
| community-mediated query expansion | Retrieval strategy | returns existing information；no semantic edge implied |
| cluster as Organization starting set | D-474 graph-guided candidate formation | seed only；Agent/behavior may expand or reject |
| reusable thematic explanation from members | D-472 provenance-preserving n-ary synthesis | derived Block only when independently useful and source basis retained |
| new precise relation discovered while analyzing | owning linking/evolution/evidence behavior | ordinary validated Relation，not copied from co-membership |

An AI-generated community name/summary is therefore ambiguous by packaging。If it only makes a live topic page readable，it is a
derived Application projection。If it states a stable、independently reusable synthesis that later users should retrieve without
repeating analysis，it must pass D-472 qualification and preserve member contribution、scope、disagreement and uncertainty。

## Candidate Formation，Not Candidate Authority

Community detection is a strong example of a deterministic or low-cost candidate mechanism before open-world semantic judgment：

```text
structural cluster / bridge result
  -> seed one exact Organization behavior
  -> Resolver + graph exploration + behavior SOP
  -> linking / synthesis / evolution proposal or no-op
```

The cluster does not bound the internal Organization Agent's exploration and does not prove that members should be linked or
synthesized。It prioritizes attention；D-493 classifies this D-474/D-481 route as a behavior-specific heuristic，not Product
semantics or another Organization method。

## Extension Implication

D-490 makes this a useful extensibility case without choosing a design。Different graph-analysis projections or algorithms could
eventually be supplied by Core or an Extension and consumed by retrieval or an Organization behavior。The contribution must name
its exact projection/result semantics；a generic “Extension may reorganize the graph” hook is unnecessary and unsafe as a Product
contract。

Whether graph analysis is delivered by an Extension does not change its authority：rebuildable cluster output remains a
projection，while persistent graph changes still belong to an exact Organization behavior and ordinary graph validation。

## Accepted Product Boundary

D-491 closes Community Detection with no independent Organization method and accepts three returns：

1. structural communities/centrality are model-relative、rebuildable graph-analysis projections for browse/query；
2. community results may seed a D-493-classified candidate heuristic but never prove or bound a semantic graph change；
3. a durable thematic summary routes to D-472 synthesis，while live names/summaries remain Application projections。

No Community node/type、canonical membership、single-partition ontology、Louvain/PageRank contract、global Entity projection、
periodic job、AI topic naming or automatic graph rewrite is approved。
