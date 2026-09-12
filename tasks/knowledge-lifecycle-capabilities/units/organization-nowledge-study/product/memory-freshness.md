# Product Study: Nowledge Memory Freshness / Decay

- **State**: closed under D-489 and reclassified by D-493；use salience is an optional scoped heuristic，not Product authority。
- **Evidence**: [Nowledge Memory Freshness](../evidence/nowledge-memory-freshness.md)。
- **Decision authority**: [D-489](../../../decisions/D481-D490.md)、
  [D-493](../../../decisions/D491-D500.md)。

## Concrete Product Cases

Consider four equally old information units：

1. a deployment decision was explicitly superseded yesterday；
2. a rarely used cryptographic recovery procedure remains authoritative and applicable；
3. an incorrect note is frequently returned because it already ranks highly；
4. an old incident record exactly matches a query asking what happened in that historical period。

One age/access score cannot preserve the distinctions。The first is a scoped currentness/evolution question；the second should
not become inapplicable through disuse；the third exposes a ranking feedback loop rather than evidence；the fourth is highly
relevant precisely because the query asks for old information。

## What Nowledge Does

Nowledge maintains two independent scores per Memory：

- a decay score combining time since interaction、access frequency and an importance floor；
- a confidence score that only grows from access/search/click/read signals、EVOLVES links and Crystal membership。

Both are secondary inputs to search ranking，while semantic relevance remains dominant。A daily refresh recomputes cached
scores without rewriting、merging、archiving or deleting Memory content。Historical/temporal queries may bypass ordinary decay
pressure。

This is primarily a use-prior mechanism packaged under Background Intelligence，not evidence that elapsed time itself performs
Organization。

## Five Meanings Hidden By “Freshness”

| Meaning | Question | Authority / owner | Durable graph effect |
| --- | --- | --- | --- |
| projection compatibility | does a retrieval record still represent its Block/Relation rows？ | retrieval support owner | none；rebuildable projection |
| temporal query relevance | does event/record time match this query's requested period？ | query execution | none |
| use salience | does past scoped use predict likely near-term reuse？ | application/retrieval profile | none by default |
| semantic currentness | is this information still applicable under a scoped authority/model？ | supersession/refinement evolution model | model Relation/state transition |
| epistemic support | what evidence supports、challenges or qualifies this assertion？ | evidence stance / provenance-preserving synthesis | explicit Relations and source basis |

Current InKCre already uses `freshness` for the first meaning：semantic/lexical derived records must agree with database-row
timestamps，and retrieval owns those projections and ranking。That term cannot be reused as a claim that information became old、
false or less useful。Storage bytes may also change without a Block-row timestamp，so even projection compatibility is explicitly
not universal content freshness。

## Past Use Predicts Future Use，But Only As A Prior

The transferable idea behind decay is valid and matches the accepted temporal limitation of Organization：past use can predict
future use even though the actual future query is unknown。Its legitimate forms include：

- a scoped retrieval profile may use interaction history as one subordinate ranking prior；
- repeated co-use may seed candidate formation for an existing linking/synthesis behavior；
- Product design may use observed failures/use patterns to justify whether one reusable Organization distinction is worth
  producing。

None makes usage a semantic or truth authority。The consumer/profile scope matters：a globally popular item may be irrelevant to
one use context，and one consumer's repeated use should not silently reorganize neutral information for every other consumer。

## Exposure Is Not Evidence

Nowledge counts search appearances as light access and includes access、appearance、click and reading time in confidence。Those
signals demonstrate exposure or use，not whether the content is true、applicable or independently corroborated。If ranking causes
an item to appear，and appearance raises its future score，the projection can reinforce its own prior output。

In InKCre terms：

```text
retrieval exposure
  -> may update scoped use telemetry
  -> may alter a future application ranking prior
  -X-> does not support the information's assertion
  -X-> does not create evolution currentness
```

`confirms` evidence may contribute to an evidence projection only under its model's source/scope law。`enriches` lineage、Crystal
membership or high access count cannot be collapsed into one monotonic epistemic confidence scalar without losing their distinct
meanings。

## Organization Boundary

Memory Freshness exposes no independent Organization method so far：

- elapsed time or interaction changes a use-facing ranking projection；
- query-time temporal intent selects the relevant time lens；
- semantic obsolescence routes to evolution only when a model establishes continuity、scope and authority；
- support/uncertainty routes to evidence stance or provenance-preserving synthesis；
- use patterns can prioritize candidates for an existing behavior but do not authorize its graph proposal。

A deterministic daily score refresh is projection maintenance，not Organization merely because Nowledge lists it under
Background Intelligence。Likewise，an importance floor is a ranking-policy input；it does not make `importance` an intrinsic
information property or Organization-owned scalar。

## Accepted Product Boundary

D-489 closes Memory Freshness / Decay with no independent Organization transfer。D-493 classifies the use-history portions as
optional retrieval/behavior heuristics and retains these boundaries：

1. separate projection compatibility、temporal relevance、use salience、semantic currentness and epistemic support；
2. use history may be a scoped、subordinate forecast prior or candidate seed，never semantic/truth authority；
3. only model-owned evolution/evidence Relations create durable currentness/support distinctions，while decay/confidence scores、
   daily refresh and importance floor remain downstream projection choices。

No score fields、30-day curve、global access counter、confidence formula、daily job、importance floor、archive threshold or
search-ranking contract is approved。
