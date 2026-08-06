# Semantic Retrieval Contract

> [Technical design index](index.md)

## T-015 Retrieval Result、Score And Filters（approved by D-113–D-116）

### Manager input

```text
SemanticRetrievalManager.retrieve(
  query: non-empty text,
  profile: EmbeddingProfile reference | null,
  options: VectorRetrievalOptions,
) -> SemanticRetrievalResult

VectorRetrievalOptions
  limit: positive integer = 20（public maximum 100）
  min_score: finite float [-1, 1] | null = null
  entity_types: set["block" | "relation"] = both
```

- null `profile` selects the deployment default through D-110；an explicit reference bypasses only default selection，not
  Profile/model/provider validation。
- query is text only。The legacy block-ID “more like this” path is a distinct similarity operation and has not been proven
  by the semantic-query/Agent journey。
- MVP exposes only filters shared by the graph result contract。Resolver/source/time/property filters remain future
  pressure；do not mix feature retrieval or source-specific predicates into the first semantic API。
- D-115 freezes `entity_types` as the only MVP candidate-filter dimension；the set is non-empty and defaults to both。
- D-116 freezes bounded top-k retrieval，optional-null score threshold and no cursor/offset pagination。More than the
  useful top results is query/semantic-preparation quality pressure，not a traversal use case；concurrent graph or embedding
  maintenance may also legitimately change later rankings。

### Comparison and score（approved by D-114）

- MVP performs exact cosine comparison over fresh，dimension-compatible records in one Profile。It does not expose a
  one-value metric selector merely to claim extensibility。
- public `score = 1 - cosine_distance`，so larger is better and `min_score` is caller-readable。Score is not confidence or
  probability and is comparable only within the same query/Profile/metric execution。
- candidate vectors and the query vector must be finite and non-zero for cosine comparison。Invalid provider output fails
  before persistence/query rather than producing NaN ordering。
- Block and Relation candidates are compared in the same vector space，merged into one global descending score order and
  then globally limited。Exact ties use deterministic `entity_type` then entity ID ordering only for repeatability，not as
  relevance evidence。

### Result（approved by D-113）

```text
SemanticRetrievalResult
  profile: EmbeddingProfile reference
  metric: "cosine"
  matches: SemanticRetrievalMatch[]

BlockSemanticRetrievalMatch
  type: "block"
  entity: BlockModel
  score: float

RelationSemanticRetrievalMatch
  type: "relation"
  entity: RelationModel
  score: float
```

- the result returns existing graph entities，not chunks、segments or a new target domain object。The discriminated match
  wrapper carries use-derived ranking metadata without taking identity/authority away from Block or Relation。
- return the full ordinary entity row so Relation matches are immediately navigable through `from_` / `to_` and Block
  matches retain resolver/storage/content references。Do not duplicate resolver `get_text()` / Relation projection in the
  result；a consumer that needs solved text resolves the returned entity through the ordinary graph capability。
- expose one score authority，not redundant score + distance fields。The result-level Profile/metric makes that score
  interpretable without repeating them per match。
- missing/stale/unavailable records are simply absent from comparison。A successful query with no qualifying candidates
  returns an empty `matches` list；configuration/provider/query-input failures remain explicit errors。

